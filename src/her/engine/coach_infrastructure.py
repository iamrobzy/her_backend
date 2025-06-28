import datetime
import os
import json
import requests
from dotenv import load_dotenv
from .prompt_builder import build_prompt, get_first_message
from typing import Optional
from sqlalchemy.orm import Session

from her.platform.db import Session
from her.platform.db.models import Conversation

class CoachInfrastructure:
    CONVERSATION_IDS_FILE = "conversation_ids.json"
    
    ONBOARDING_PROMPT_FILE = "src/prompts/personality/cute_pushy_personality.md"
    FOLLOW_UP_PROMPT_FILE = "src/prompts/personality/cute_pushy_personality.md"
    ONBOARDING_FIRST_MESSAGE_PROMPT_FILE = "src/prompts/onboarding/first_message_onboarding.md"
    FOLLOW_UP_FIRST_MESSAGE_PROMPT_FILE = "src/prompts/follow_up/first_message_follow_up.md"
    
    ATOMIC_HABITS_PROMPT_FILE = "src/prompts/books/atomic_habits_prompt.md"
    
    # def create_system_prompt(self, flow_stage_file_name: str):
    #     system_prompt = ""
        
    #     FILES = [
    #         self.ATOMIC_HABITS_PROMPT_FILE,
    #     ]
        
    #     with open(flow_stage_file_name, "r") as f:
    #         system_prompt += f.read()
    #         system_prompt += "\n\n"
            
    #     for file_name in FILES:
    #         with open(file_name, "r") as f:
    #             system_prompt += f.read()
    #             system_prompt += "\n\n"
                
    #     return system_prompt
        
            
    def __init__(
        self,
        elevenlabs_api_key: str,
        agent_id: str,
        agent_phone_number_id: str,
        to_number: str,
    ):
        self.elevenlabs_api_key = elevenlabs_api_key
        self.agent_id = agent_id
        self.agent_phone_number_id = agent_phone_number_id
        self.to_number = to_number
        self.__init_conversation_ids_file()
        
    def __init_conversation_ids_file(self):
        if not os.path.exists(self.CONVERSATION_IDS_FILE):
            with open(self.CONVERSATION_IDS_FILE, "w") as f:
                json.dump([], f)
                
    def _save_conversation_id(self, conversation_id: str) -> None:
        """Append the conversation ID to the file as part of a list."""
        try:
            # Try to read existing IDs
            with open(self.CONVERSATION_IDS_FILE, "r") as f:
                conversation_ids = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            conversation_ids = []
        
        # Append new ID
        conversation_ids.append(conversation_id)
        
        # Write back the updated list
        with open(self.CONVERSATION_IDS_FILE, "w") as f:
            json.dump(conversation_ids, f)
            
    def _get_last_conversation_id(self):
        with open(self.CONVERSATION_IDS_FILE, "r") as f:
            conversation_ids = json.load(f)
            
        return conversation_ids[-1]
            

    def outbound_call(self, first_message: str, prompt: str, context: Optional[str] = None) -> dict:
        curl_url = "https://api.elevenlabs.io/v1/convai/twilio/outbound_call"
        curl_headers = {
            "Xi-Api-Key": self.elevenlabs_api_key,
            "Content-Type": "application/json",
        }
        
        if context:
            prompt = f"{prompt}\n\n Current user context: {context}"

        curl_data = {
            "agent_id": self.agent_id,
            "agent_phone_number_id": self.agent_phone_number_id,
            "to_number": self.to_number,
            "conversation_initiation_client_data": {
                "conversation_config_override": {
                    "agent": {
                        "prompt": {"prompt": prompt},
                        "first_message": first_message,
                    }
                }
            },
        }

        curl_response = requests.post(
            curl_url, headers=curl_headers, data=json.dumps(curl_data)
        )
        
        self._save_conversation_id(curl_response.json()["conversation_id"])
        
        return curl_response.json()
    
    
    def get_last_conversation_transcript(self):
        last_conversation_id = self._get_last_conversation_id()
        
        curl_url = f"https://api.elevenlabs.io/v1/convai/conversations/{last_conversation_id}"
        curl_headers = {
            "Xi-Api-Key": self.elevenlabs_api_key,
            "Content-Type": "application/json",
        }
        
        response = requests.get(
            curl_url, headers=curl_headers
        ).json()
        
        transcript = response["transcript"]
        print(f"Transcript of last conversation: {transcript}")
        return transcript
    
    def get_conversation_transcript_by_id(self, conversation_id: str) -> str:
        curl_url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
        curl_headers = {
            "Xi-Api-Key": self.elevenlabs_api_key,
            "Content-Type": "application/json",
        }
        
        response = requests.get(
            curl_url, headers=curl_headers
        ).json()
        
        print(response)
        
        return response["transcript"]
    
    def get_transcripts_by_ids(self, conversation_ids):
        return [self.get_conversation_transcript_by_id(conversation_id) for conversation_id in conversation_ids]
    
    def get_last_conversation_ids(self, number_of_conversations=10):
        curl_url = f"https://api.elevenlabs.io/v1/convai/conversations"
        curl_headers = {
            "Xi-Api-Key": self.elevenlabs_api_key,
            "Content-Type": "application/json",
        }
        
        curl_query_params = {
            "page_size": number_of_conversations
        }
        
        response = requests.get(
            curl_url, headers=curl_headers, params=curl_query_params
        ).json()
        
        return [(conversation["conversation_id"], datetime.datetime.fromtimestamp(conversation["start_time_unix_secs"])) for conversation in response["conversations"]]
    
    def make_onboarding_call(self) -> dict:
        prompt = build_prompt("onboarding")
        first_message = get_first_message("onboarding")
        return self.outbound_call(first_message, prompt)
    
    def make_follow_up_call(self) -> dict:
        prompt = build_prompt("followup")
        first_message = get_first_message("followup")
        
        # Get last conversation transcript for context
        with Session() as db:
            last_conv = db.query(Conversation)\
                .filter(Conversation.channel == "phone")\
                .order_by(Conversation.started.desc())\
                .first()
            context = last_conv.transcript if last_conv else None
            
        return self.outbound_call(first_message, prompt, context)
    
    
    def hard_coded_future_follow_up_call(self):
        FUTURE_FOLLOW_UP_FIRST_MESSAGE_PROMPT_FILE = "src/prompts/follow_up/future_follow_up_first_message.md"
        HARD_CODED_FUTURE_CONTEXT = "src/prompts/follow_up/hard_coded_future_context.md"
        
        with open(self.FOLLOW_UP_FIRST_MESSAGE_PROMPT_FILE, "r") as f:
            first_message = f.read()
            
        with open(HARD_CODED_FUTURE_CONTEXT, "r") as f:
            context = f.read()
            
        prompt = build_prompt("followup")
        
        return self.outbound_call(first_message, prompt, context)