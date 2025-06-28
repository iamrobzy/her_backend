from abc import ABC, abstractmethod

class Channel(ABC):
    channel_type: str

    @abstractmethod
    async def start_conversation(self, flow_type: str, phone_number: str | None,
                                 prompt: str, first_message: str) -> dict:
        ...

    @abstractmethod
    async def get_transcript(self, conversation_id: str) -> str:
        ...
