import json
import os
import uuid

import modal
import requests
from elevenlabs import ElevenLabs
from zep_cloud.client import Zep

from src.db.llm_model import populate
from src.utils.api import format_error_response
from src.utils.zep import convert_to_zep_messages, query_zep

app = modal.App("HER")

# Create the image with all requirements
image = modal.Image.debian_slim().pip_install(
    [
        "fastapi[standard]",
        "zep-cloud",
        "elevenlabs",
        "python-dotenv",
        "openai",
    ]
)
image = image.add_local_dir("src", "/root/src")
image = image.add_local_python_source("src")


@app.function(image=image, secrets=[modal.Secret.from_name("HER")])
@modal.fastapi_endpoint()
async def add_user(first_name, last_name, user_id, email):
    try:
        zep = Zep(api_key=os.environ.get("ZEP_API_KEY"))
        zep.user.add(
            user_id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        return {
            "status": "success",
            "data": {
                "user_id": user_id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
            },
            "message": "User added successfully",
        }
    except Exception as e:
        return format_error_response(str(e))


@app.function(image=image, secrets=[modal.Secret.from_name("HER")])
@modal.fastapi_endpoint()
async def update_user(first_name, last_name, user_id, email):
    try:
        zep = Zep(api_key=os.environ.get("ZEP_API_KEY"))
        zep.user.update(
            user_id=user_id,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )
        return {
            "status": "success",
            "data": {
                "user_id": user_id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
            },
            "message": "User updated successfully",
        }
    except Exception as e:
        return format_error_response(str(e))


@app.function(image=image, secrets=[modal.Secret.from_name("HER")])
@modal.fastapi_endpoint(method="POST")
async def add_conversation(session_id, user_id, messages=None):
    try:
        print(
            f"Adding conversation for session_id: {session_id}, "
            f"user_id: {user_id}"
        )
        print(f"Received messages: {messages}")

        zep = Zep(api_key=os.environ.get("ZEP_API_KEY"))
        print("Zep client initialized successfully")

        zep.memory.add_session(
            session_id=session_id,
            user_id=user_id,
        )
        print(f"Session {session_id} added to Zep successfully")

        if messages:
            # Use directly provided messages
            print("Using provided messages...")
            try:
                converted_messages = convert_to_zep_messages(messages)
                print(
                    f"Successfully converted {len(converted_messages)} "
                    f"messages"
                )
            except Exception as e:
                error_msg = f"Failed to convert messages: {str(e)}"
                print(f"Error: {error_msg}")
                return format_error_response(error_msg, status_code=400)
        else:
            # Fetch from ElevenLabs if no messages provided
            print("No messages provided, fetching from ElevenLabs...")
            client = ElevenLabs(
                api_key=os.environ.get("ELEVENLABS_API_KEY"),
            )
            print("ElevenLabs client initialized successfully")

            print(
                f"Fetching conversation from ElevenLabs with "
                f"conversation_id: {session_id}"
            )
            conversation = client.conversational_ai.get_conversation(
                conversation_id=session_id,
            )
            print(f"ElevenLabs conversation retrieved: {conversation}")

            if not conversation:
                error_msg = (
                    f"No conversation found for conversation_id: {session_id}"
                )
                print(f"Error: {error_msg}")
                return format_error_response(error_msg, status_code=404)

            print("Converting conversation to Zep messages...")
            converted_messages = convert_to_zep_messages(conversation)

        if not converted_messages:
            error_msg = (
                "Failed to convert conversation to Zep messages: "
                "no messages returned"
            )
            print(f"Error: {error_msg}")
            return format_error_response(error_msg, status_code=400)

        print(f"Converted messages count: {len(converted_messages)}")

        # Log each message
        for i, msg in enumerate(converted_messages):
            print(
                f"Message {i+1}: role_type={msg.role_type}, "
                f"content_length={len(msg.content)}"
            )

        print(f"Adding {len(converted_messages)} messages to Zep memory")
        zep.memory.add(session_id=session_id, messages=converted_messages)
        print("Messages added to Zep memory successfully")

        return {
            "status": "success",
            "data": {"session_id": session_id, "user_id": user_id},
            "message": "Conversation added successfully",
        }
    except ValueError as e:
        error_msg = f"Invalid conversation data: {str(e)}"
        print(f"Error: {error_msg}")
        import traceback

        traceback.print_exc()
        return format_error_response(error_msg, status_code=400)
    except Exception as e:
        print(f"Error in add_conversation: {str(e)}")
        import traceback

        traceback.print_exc()
        return format_error_response(str(e))


@app.function(image=image, secrets=[modal.Secret.from_name("HER")])
@modal.fastapi_endpoint()
async def get_context_from_a_session(session_id):
    try:
        zep = Zep(api_key=os.environ.get("ZEP_API_KEY"))
        memory = zep.memory.get(session_id=session_id)
        context_string = memory.context
        return {
            "status": "success",
            "data": {"session_id": session_id, "context": context_string},
            "message": "Context retrieved successfully",
        }
    except Exception as e:
        return format_error_response(str(e))


@app.function(image=image, secrets=[modal.Secret.from_name("HER")])
@modal.fastapi_endpoint()
async def get_conversation_context(user_id, agenda):
    try:
        print(f"Starting get_conversation_context for user_id: {user_id}")
        print(f"Agenda: {agenda}")

        session_id = uuid.uuid4().hex
        print(f"Generated new session_id: {session_id}")

        zep = Zep(api_key=os.environ.get("ZEP_API_KEY"))
        print("Successfully initialized Zep client")
        context_string = query_zep(user_id, session_id, agenda, zep)

        return {
            "status": "success",
            "data": {
                "session_id": session_id,
                "user_id": user_id,
                "context": context_string,
            },
            "message": "Conversation context retrieved successfully",
        }
    except Exception as e:
        print(f"Error in get_conversation_context: {str(e)}")
        import traceback

        traceback.print_exc()
        return format_error_response(str(e))


@app.function(image=image, secrets=[modal.Secret.from_name("HER")])
async def get_advice(graph_context):
    print(
        f"Starting get_advice with context length: {len(str(graph_context))}"
    )
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": (
                    "Give expert advice to the user based on domain "
                    "knowledge. Give a detailed answer given "
                    "your sources. No introduction needed."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Give me advice on how to achieve the following goals "
                    f"and milestones: {graph_context}"
                ),
            },
        ],
    }
    headers = {
        "Authorization": "Bearer " + os.getenv("PPXL_API_KEY"),
        "Content-Type": "application/json",
    }
    print("Sending request to Perplexity API")
    response = requests.request("POST", url, json=payload, headers=headers)
    print(
        f"Received response from Perplexity API: "
        f"status_code={response.status_code}"
    )
    response_json = json.loads(response.content)
    citations, advice = (
        response_json["citations"],
        response_json["choices"][0]["message"]["content"],
    )
    print(f"Extracted advice with length: {len(advice)}")
    return citations, advice


@app.function(image=image, secrets=[modal.Secret.from_name("HER")])
@modal.fastapi_endpoint(method="POST")
async def generate_milestones(user_id):
    print(f"Starting generate_milestones for user_id: {user_id}")
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY not found in environment variables")
        return format_error_response("OpenAI API key not found")

    try:
        print("Generating conversation context with graph query")
        graph_query = (
            "What are the goals and milestones of this user? "
            "How much time does the user plan to dedicate to "
            "execute the goals?"
        )

        print(f"Calling get_conversation_context for user_id: {user_id}")
        session_id = uuid.uuid4().hex
        print(f"Generated new session_id: {session_id}")
        zep = Zep(api_key=os.environ.get("ZEP_API_KEY"))
        graph_context = query_zep(user_id, session_id, graph_query, zep)
        print(f"Received graph_context with data: {graph_context}")

        print("Calling get_advice with graph context")
        citations, advice = get_advice.remote(graph_context)
        print(f"Received advice with length: {len(advice)}")

        print("Calling populate with advice to generate goal structure")
        goal = populate(advice, OPENAI_API_KEY)
        print(
            f"Generated goal with title: "
            f"{goal.title if hasattr(goal, 'title') else 'No title'}"
        )

        return {
            "status": "success",
            "data": {
                "user_id": user_id,
                "goal": goal,
            },
            "message": "Agenda generated successfully",
        }
    except Exception as e:
        print(f"Error in generate_milestones: {str(e)}")
        import traceback

        traceback.print_exc()
        return format_error_response(str(e))


# Todo: implement a tool to get some context/information live in conversation
# ? if user says e.g. "today i want to talk about somthin else,
# ? then change
# ? context"
