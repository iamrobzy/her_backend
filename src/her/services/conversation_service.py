from datetime import datetime, timezone
from typing import Optional

from her.engine.channels.phone import PhoneChannel, Channel
from her.platform.db import Session
from her.platform.db.models import User, Conversation
from her.engine.prompt_builder import build_prompt, get_first_message
from her.platform.settings import settings

class ConversationService:
    def __init__(self, channel_type: str = "phone"):
        self.channel = self._get_channel(channel_type)

    def _get_channel(self, kind: str) -> Channel:
        if kind == "phone":
            return PhoneChannel()
        raise ValueError(f"Unknown channel: {kind}")

    async def trigger(
        self,
        user_id: str,
        flow_type: str,
        phone: Optional[str] = None,
    ) -> dict:
        with Session.begin() as db:
            user = db.get(User, user_id) or User(id=user_id, phone=phone)
            if not user.phone:
                raise ValueError("Phone number required for phone channel")
            db.add(user)

        prompt, first = build_prompt(flow_type), get_first_message(flow_type)
        result = await self.channel.start_conversation(
            flow_type, phone or user.phone, prompt, first
        )

        with Session.begin() as db:
            db.add(
                Conversation(
                    id=result["conversation_id"],
                    user_id=user_id,
                    channel=self.channel.channel_type,
                    flow=flow_type,
                    started=datetime.now(timezone.utc),
                )
            )

        return result          # caller decides what to do with it
