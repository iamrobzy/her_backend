import datetime
import os
import json
import requests
from dotenv import load_dotenv

class CoachInfrastructure:
    CONVERSATION_IDS_FILE = "conversation_ids.json"
    
    ONBOARDING_PROMPT_FILE = "src/prompts/personality/personality.md"
    FOLLOW_UP_PROMPT_FILE = "src/prompts/follow_up/follow_up.md"
    ONBOARDING_FIRST_MESSAGE_PROMPT_FILE = "src/prompts/personality/personality.md"
    FOLLOW_UP_FIRST_MESSAGE_PROMPT_FILE = "src/prompts/follow_up/first_message_follow_up.md"
    
    def __init__(self):
        load_dotenv()
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.agent_id = os.getenv("AGENT_ID")
        self.agent_phone_number_id = os.getenv("AGENT_PHONE_NUMBER_ID")
        self.to_number = os.getenv("TO_NUMBER")
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
            

    def outbound_call(self, first_message, prompt, context, outbound_agent_id, agent_phone_number_id, to_number):
        curl_url = "https://api.elevenlabs.io/v1/convai/twilio/outbound_call"
        curl_headers = {
            "Xi-Api-Key": os.getenv("ELEVENLABS_API_KEY"),
            "Content-Type": "application/json",
        }
        
        if context:
            prompt = f"{prompt}\n\n Current user context: {context}"

        curl_data = {
            "agent_id": outbound_agent_id,
            "agent_phone_number_id": agent_phone_number_id,
            "to_number": to_number,
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
            "Xi-Api-Key": os.getenv("ELEVENLABS_API_KEY"),
            "Content-Type": "application/json",
        }
        
        response = requests.get(
            curl_url, headers=curl_headers
        ).json()
        
        transcript = response["transcript"]
        print(f"Transcript of last conversation: {transcript}")
        return transcript
    
    def get_conversation_transcript_by_id(self, conversation_id):
        curl_url = f"https://api.elevenlabs.io/v1/convai/conversations/{conversation_id}"
        curl_headers = {
            "Xi-Api-Key": os.getenv("ELEVENLABS_API_KEY"),
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
            "Xi-Api-Key": os.getenv("ELEVENLABS_API_KEY"),
            "Content-Type": "application/json",
        }
        
        curl_query_params = {
            "page_size": number_of_conversations
        }
        
        response = requests.get(
            curl_url, headers=curl_headers, params=curl_query_params
        ).json()
        
        return [(conversation["conversation_id"], datetime.datetime.fromtimestamp(conversation["start_time_unix_secs"])) for conversation in response["conversations"]]
    
    def make_onboarding_call(self):
        with open(self.ONBOARDING_FIRST_MESSAGE_PROMPT_FILE, "r") as f:
            first_message = f.read()
        with open(self.ONBOARDING_PROMPT_FILE, "r") as f:
            prompt = f.read()
            
        return self.outbound_call(first_message, prompt, None, self.agent_id, self.agent_phone_number_id, self.to_number)
    
    def make_follow_up_call(self):
        with open(self.FOLLOW_UP_FIRST_MESSAGE_PROMPT_FILE, "r") as f:
            first_message = f.read()
        with open(self.FOLLOW_UP_PROMPT_FILE, "r") as f:
            prompt = f.read()
            
        context = self.get_last_conversation_transcript()
        
        return self.outbound_call(first_message, prompt, context, self.agent_id, self.agent_phone_number_id, self.to_number)