import os
import uuid

import modal
from elevenlabs import ElevenLabs
from zep_cloud import Message
from zep_cloud.client import Zep

from src.utils.api import format_error_response
from src.utils.zep import convert_to_zep_messages
from src.db.llm_model import populate

app = modal.App("HER")

# Create the image with all requirements
image = modal.Image.debian_slim().pip_install(
    [
        "fastapi[standard]",
        "zep-cloud",
        "elevenlabs",
        "python-dotenv",
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
@modal.fastapi_endpoint()
async def add_conversation(session_id, user_id):
    try:
        zep = Zep(api_key=os.environ.get("ZEP_API_KEY"))

        zep.memory.add_session(
            session_id=session_id,
            user_id=user_id,
        )

        client = ElevenLabs(
            api_key=os.environ.get("ELEVENLABS_API_KEY"),
        )

        conversation = client.conversational_ai.get_conversation(
            conversation_id=session_id,
        )
        messages = convert_to_zep_messages(conversation)
        zep.memory.add(session_id=session_id, messages=messages)

        return {
            "status": "success",
            "data": {"session_id": session_id, "user_id": user_id},
            "message": "Conversation added successfully",
        }
    except Exception as e:
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
        session_id = uuid.uuid4().hex
        zep = Zep(api_key=os.environ.get("ZEP_API_KEY"))
        zep.memory.add_session(user_id=user_id, session_id=session_id)
        zep.memory.add(
            session_id=session_id,
            messages=[Message(role_type="system", content=agenda)],
        )
        memory = zep.memory.get(session_id=session_id)
        context_string = memory.context
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
        return format_error_response(str(e))


@app.function(image=image, secrets=[modal.Secret.from_name("HER")])
async def get_advice(graph_context):
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
            "model": "sonar",
            "messages": [
                {
                "role": "system",
                "content": "Give expert advice to the user based on domain knowledge. Give a detailed answer given your sources. No introduction needed."
            },
            {
                "role": "user",
                "content": f"Give me advice on the to achieve the following goals and milestones: {graph_context}"
            }
        ]
    }
    headers = {
        "Authorization": "Bearer " + os.getenv("PPXL_API_KEY"),
        "Content-Type": "application/json"
    }
    response = requests.request("POST", url, json=payload, headers=headers)
    response_json = json.loads(response.content)
    citations, advice = response_json['citations'], response_json['choices'][0]['message']['content']
    return citations, advice


@app.function(image=image, secrets=[modal.Secret.from_name("HER")])
@modal.fastapi_endpoint()
async def generate_agenda(user_id):

    graph_query = "What are the goals and milestones of this user? How much time does the user plan to dedicate to execute the goals?"
    graph_context = get_conversation_context(user_id=user_id, agenda=graph_query)
    citations, advice = get_advice(graph_context)
    goal = populate(advice)
    return goal


# Todo: implement a tool to get some context/information live in conversation
# ? if user says e.g. "today i want to talk about somthin else,
# ? then change
# ? context"
