from datetime import datetime, timezone

from graphiti_core import Graphiti
from graphiti_core.embedder.gemini import GeminiEmbedder, GeminiEmbedderConfig
from graphiti_core.llm_client.gemini_client import GeminiClient, LLMConfig
from graphiti_core.nodes import EpisodeType
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF


def conversation_to_episode(conversation):
    """Convert an ElevenLabs conversation to a Graphiti episode format.

    Args:
        conversation: An ElevenLabs conversation object

    Returns:
        dict: An episode dictionary ready for Graphiti ingestion
    """
    # Extract conversation name/description
    agent_id = (
        conversation.agent_id
        if hasattr(conversation, "agent_id")
        else "Unknown Agent"
    )

    # Build conversation content in message format
    content = ""
    if hasattr(conversation, "transcript") and conversation.transcript:
        for message in conversation.transcript:
            role = message.role if hasattr(message, "role") else "unknown"
            msg_text = message.message if hasattr(message, "message") else ""
            content += f"{role}: {msg_text}\n\n"

    # Add metadata as a section at the end of content
    content += "\n\n--- METADATA ---\n"

    # Add basic conversation info
    if hasattr(conversation, "conversation_id"):
        content += f"conversation_id: {conversation.conversation_id}\n"
    if hasattr(conversation, "agent_id"):
        content += f"agent_id: {conversation.agent_id}\n"
    if hasattr(conversation, "status"):
        content += f"status: {conversation.status}\n"

    # Add analysis summary if available
    if hasattr(conversation, "analysis") and hasattr(
        conversation.analysis, "transcript_summary"
    ):
        content += f"summary: {conversation.analysis.transcript_summary}\n"

    # Add metadata details if available
    if hasattr(conversation, "metadata"):
        meta = conversation.metadata
        if hasattr(meta, "start_time_unix_secs"):
            content += f"start_time: {meta.start_time_unix_secs}\n"
        if hasattr(meta, "call_duration_secs"):
            content += f"call_duration: {meta.call_duration_secs}\n"
        if hasattr(meta, "main_language"):
            content += f"language: {meta.main_language}\n"

    # Create the episode object
    episode = {
        "content": content,
        "type": EpisodeType.message,
        "description": f"ElevenLabs conversation with {agent_id}",
    }

    return episode


def init_graphiti(
    neo4j_uri,
    neo4j_user,
    neo4j_password,
    google_api_key,
    embedding_model="embedding-001",
    llm_model="gemini-2.0-flash",
):
    return Graphiti(
        neo4j_uri,
        neo4j_user,
        neo4j_password,
        llm_client=GeminiClient(
            config=LLMConfig(api_key=google_api_key, model=llm_model)
        ),
        embedder=GeminiEmbedder(
            config=GeminiEmbedderConfig(
                api_key=google_api_key, embedding_model=embedding_model
            )
        ),
    )


async def add_conversation_to_graphiti(
    conversation, neo4j_uri, neo4j_user, neo4j_password, google_api_key
):
    """
    Add an ElevenLabs conversation to Graphiti as an episode.

    Args:
        conversation: The ElevenLabs conversation object
        neo4j_uri: Neo4j database URI
        neo4j_user: Neo4j database username
        neo4j_password: Neo4j database password
        google_api_key: Google API key for Gemini models

    Returns:
        bool: True if successful, False otherwise
    """
    # Initialize Graphiti with the provided connection parameters
    graphiti = init_graphiti(
        neo4j_uri, neo4j_user, neo4j_password, google_api_key
    )

    try:
        # Initialize the graph database indices if needed
        await graphiti.build_indices_and_constraints()

        # Convert the conversation to an episode format
        episode = conversation_to_episode(conversation)

        # Extract conversation ID for the episode name
        conversation_id = (
            conversation.conversation_id
            if hasattr(conversation, "conversation_id")
            else "unknown_id"
        )

        # Add the episode to Graphiti
        await graphiti.add_episode(
            name=f"ElevenLabs Conversation {conversation_id}",
            episode_body=episode["content"],
            source=episode["type"],
            source_description=episode["description"],
            reference_time=datetime.now(timezone.utc),
        )

        print(f"Successfully added conversation {conversation_id} to Graphiti")
        return True

    except Exception as e:
        print(f"Error adding conversation to Graphiti: {str(e)}")
        return False

    finally:
        # Close the connection
        await graphiti.close()
        print("Graphiti connection closed")


async def search_graphiti(
    query,
    center_node_uuid=None,
    neo4j_uri=None,
    neo4j_user=None,
    neo4j_password=None,
    google_api_key=None,
):
    """
    Search for information in Graphiti.

    Args:
        query: Search query string
        center_node_uuid: Optional UUID to use as center node for reranking
        neo4j_uri: Neo4j database URI
        neo4j_user: Neo4j database username
        neo4j_password: Neo4j database password
        google_api_key: Google API key for Gemini models

    Returns:
        dict: Search results
    """
    # Initialize Graphiti with the provided connection parameters
    graphiti = init_graphiti(
        neo4j_uri, neo4j_user, neo4j_password, google_api_key
    )

    try:
        # Perform the search
        if center_node_uuid:
            results = await graphiti.search(
                query, center_node_uuid=center_node_uuid
            )
        else:
            results = await graphiti.search(query)

        # Convert results to a serializable format
        serialized_results = []
        for result in results:
            result_dict = {"uuid": result.uuid, "fact": result.fact}

            if hasattr(result, "valid_at") and result.valid_at:
                result_dict["valid_from"] = (
                    result.valid_at.isoformat()
                    if hasattr(result.valid_at, "isoformat")
                    else str(result.valid_at)
                )

            if hasattr(result, "invalid_at") and result.invalid_at:
                result_dict["valid_until"] = (
                    result.invalid_at.isoformat()
                    if hasattr(result.invalid_at, "isoformat")
                    else str(result.invalid_at)
                )

            serialized_results.append(result_dict)

        return {"status": "success", "results": serialized_results}

    except Exception as e:
        print(f"Error searching Graphiti: {str(e)}")
        return {"status": "error", "message": str(e)}

    finally:
        # Close the connection
        await graphiti.close()
        print("Graphiti connection closed")


async def search_nodes(
    query,
    limit=5,
    neo4j_uri=None,
    neo4j_user=None,
    neo4j_password=None,
    google_api_key=None,
):
    """
    Search for nodes in Graphiti using the NODE_HYBRID_SEARCH_RRF recipe.

    Args:
        query: Search query string
        limit: Maximum number of results to return
        neo4j_uri: Neo4j database URI
        neo4j_user: Neo4j database username
        neo4j_password: Neo4j database password
        google_api_key: Google API key for Gemini models

    Returns:
        dict: Node search results
    """
    # Initialize Graphiti with the provided connection parameters
    graphiti = init_graphiti(
        neo4j_uri, neo4j_user, neo4j_password, google_api_key
    )

    try:
        # Use a predefined search configuration recipe and modify its limit
        node_search_config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        node_search_config.limit = limit

        # Execute the node search
        node_search_results = await graphiti._search(
            query=query,
            config=node_search_config,
        )

        # Convert results to a serializable format
        serialized_nodes = []
        for node in node_search_results.nodes:
            node_dict = {
                "uuid": node.uuid,
                "name": node.name,
                "summary": node.summary,
                "labels": list(node.labels) if hasattr(node, "labels") else [],
                "created_at": (
                    node.created_at.isoformat()
                    if hasattr(node.created_at, "isoformat")
                    else str(node.created_at)
                ),
            }

            if hasattr(node, "attributes") and node.attributes:
                node_dict["attributes"] = node.attributes

            serialized_nodes.append(node_dict)

        return {"status": "success", "nodes": serialized_nodes}

    except Exception as e:
        print(f"Error searching nodes in Graphiti: {str(e)}")
        return {"status": "error", "message": str(e)}

    finally:
        # Close the connection
        await graphiti.close()
        print("Graphiti connection closed")
