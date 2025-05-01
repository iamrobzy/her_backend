from elevenlabs import ElevenLabs


def get_conversation(api_key, conversation_id):
    client = ElevenLabs(api_key=api_key)
    conversation = client.conversational_ai.get_conversation(
        conversation_id=conversation_id
    )
    return conversation
