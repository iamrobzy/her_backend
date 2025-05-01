import os

import modal
from elevenlabs import ElevenLabs

# Create the Modal FastAPI app
app = modal.App("HER")

# Create image with dependencies and add local src directory
image = modal.Image.debian_slim().pip_install(
    ["fastapi[standard]", "elevenlabs"]
)
image = image.add_local_dir("src", "/root/src")
image = image.add_local_python_source("src")


@app.function(image=image, secrets=[modal.Secret.from_name("HER")])
@modal.fastapi_endpoint()
def print_conv(conversation_id: str):
    ELEVENLABS_API_KEY = os.environ["ELEVENLABS_API_KEY"]

    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    conversation = client.conversational_ai.get_conversation(
        conversation_id=conversation_id
    )

    print(conversation)

    return {
        "status": "listening to conversation",
        "conversation_id": conversation_id,
    }
