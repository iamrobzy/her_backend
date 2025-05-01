import os

import modal
from fastapi import Query

from src.eleven import get_conversation
from src.graphiti import (
    add_conversation_to_graphiti,
    conversation_to_episode,
    search_graphiti,
    search_nodes,
)

app = modal.App("HER")

image = modal.Image.debian_slim().pip_install(
    [
        "fastapi[standard]",
        "elevenlabs",
        "graphiti_core[google-genai]",
        "neo4j",
        "python-dotenv",
    ]
)
image = image.add_local_dir("src", "/root/src")
image = image.add_local_python_source("src")


@app.function(image=image, secrets=[modal.Secret.from_name("HER")])
@modal.fastapi_endpoint()
def print_conv(conversation_id: str):
    ELEVENLABS_API_KEY = os.environ["ELEVENLABS_API_KEY"]

    conversation = get_conversation(ELEVENLABS_API_KEY, conversation_id)

    episode = conversation_to_episode(conversation)

    print("Original conversation:")
    print(conversation)
    print("\nConverted episode:")
    print(episode)

    return {
        "status": "listening to conversation",
        "conversation_id": conversation_id,
        "episode": episode,
    }


@app.function(image=image, secrets=[modal.Secret.from_name("HER")])
@modal.fastapi_endpoint()
async def add_to_graphiti(conversation_id: str):
    ELEVENLABS_API_KEY = os.environ["ELEVENLABS_API_KEY"]

    neo4j_uri = os.environ.get("NEO4J_URI")
    neo4j_user = os.environ.get("NEO4J_USER")
    neo4j_password = os.environ.get("NEO4J_PASSWORD")
    google_api_key = os.environ.get("GOOGLE_API_KEY")

    print(
        f"NEO4J_URI: {neo4j_uri[:15]}..." if neo4j_uri else "NEO4J_URI: None"
    )  # Only show part of the URI

    if not all(
        [
            neo4j_uri,
            neo4j_user,
            neo4j_password,
            google_api_key,
            ELEVENLABS_API_KEY,
        ]
    ):
        missing = []
        if not neo4j_uri:
            missing.append("NEO4J_URI")
        if not neo4j_user:
            missing.append("NEO4J_USER")
        if not neo4j_password:
            missing.append("NEO4J_PASSWORD")
        if not google_api_key:
            missing.append("GOOGLE_API_KEY")
        if not ELEVENLABS_API_KEY:
            missing.append("ELEVENLABS_API_KEY")
        return {
            "error": f"Missing required env variables: {', '.join(missing)}"
        }

    conversation = get_conversation(ELEVENLABS_API_KEY, conversation_id)

    try:
        success = await add_conversation_to_graphiti(
            conversation=conversation,
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
            google_api_key=google_api_key,
        )

        return {
            "status": "success" if success else "error",
            "message": (
                "Conversation added to Graphiti"
                if success
                else "Failed to add conversation"
            ),
            "conversation_id": conversation_id,
        }
    except Exception as e:
        print(f"Error in add_to_graphiti: {str(e)}")
        import traceback

        traceback.print_exc()
        return {
            "status": "error",
            "message": f"Error adding conversation to Graphiti: {str(e)}",
            "conversation_id": conversation_id,
        }


@app.function(image=image, secrets=[modal.Secret.from_name("HER")])
@modal.fastapi_endpoint()
async def search(
    query: str,
    center_node_uuid: str = Query(
        None, description="Optional UUID to use as center node for reranking"
    ),
):

    neo4j_uri = os.environ.get("NEO4J_URI")
    neo4j_user = os.environ.get("NEO4J_USER")
    neo4j_password = os.environ.get("NEO4J_PASSWORD")
    google_api_key = os.environ.get("GOOGLE_API_KEY")

    if not all([neo4j_uri, neo4j_user, neo4j_password, google_api_key]):
        return {"error": "Missing required env variables for Graphiti"}

    try:
        results = await search_graphiti(
            query=query,
            center_node_uuid=center_node_uuid,
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
            google_api_key=google_api_key,
        )

        return results
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error searching Graphiti: {str(e)}",
        }


@app.function(image=image, secrets=[modal.Secret.from_name("HER")])
@modal.fastapi_endpoint()
async def search_nodes_endpoint(
    query: str,
    limit: int = Query(5, description="Maximum number of results to return"),
):

    neo4j_uri = os.environ.get("NEO4J_URI")
    neo4j_user = os.environ.get("NEO4J_USER")
    neo4j_password = os.environ.get("NEO4J_PASSWORD")
    google_api_key = os.environ.get("GOOGLE_API_KEY")

    if not all([neo4j_uri, neo4j_user, neo4j_password, google_api_key]):
        return {"error": "Missing required env variables for Graphiti"}

    try:
        results = await search_nodes(
            query=query,
            limit=limit,
            neo4j_uri=neo4j_uri,
            neo4j_user=neo4j_user,
            neo4j_password=neo4j_password,
            google_api_key=google_api_key,
        )

        return results
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error searching nodes in Graphiti: {str(e)}",
        }
