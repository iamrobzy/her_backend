from . import Channel
from her.engine.coach_infrastructure import CoachInfrastructure
from her.platform.db import Session
from her.platform.db.models import Conversation
from her.platform.settings import settings

class PhoneChannel(Channel):
    channel_type = "phone"

    async def start_conversation(self, flow_type: str, phone_number: str, prompt: str, first_message: str) -> dict:
        coach = CoachInfrastructure(
            elevenlabs_api_key=settings.elevenlabs_api_key,
            agent_id=settings.agent_id,
            agent_phone_number_id=settings.agent_phone_number_id,
            to_number=phone_number,
        )
        
        if flow_type == "onboarding":
            return coach.make_onboarding_call()
        elif flow_type == "followup":
            return coach.make_follow_up_call()
        else:
            raise ValueError(f"Unknown flow type: {flow_type}")

    async def get_transcript(self, conversation_id: str) -> str:
        coach = CoachInfrastructure(
            elevenlabs_api_key=settings.elevenlabs_api_key,
            agent_id=settings.agent_id,
            agent_phone_number_id=settings.agent_phone_number_id,
            to_number="",  # Not needed for transcript fetch
        )
        return coach.get_conversation_transcript_by_id(conversation_id)
