import os
import json
import requests
# from zep_cloud import Zep
from dotenv import load_dotenv

class CoachInfrastructure:
    def __init__(self):
        load_dotenv()
        # self.zep_client = Zep(
        #     api_key=os.getenv("ZEP_API_KEY")
        # )
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.agent_id = os.getenv("AGENT_ID")
        self.agent_phone_number_id = os.getenv("AGENT_PHONE_NUMBER_ID")
        self.to_number = os.getenv("TO_NUMBER")

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
        return curl_response.json()
    
    # TODO: change to get user context from Zep, not just from previous conversation on ElevenLabs
    def get_last_conversation_context(self):
        curl_url = f"https://api.elevenlabs.io/v1/convai/conversations/{self.last_conversation_id}"
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
    
    def make_onboarding_call(self):
        with open("src/prompts/onboarding/first_message_onboarding.md", "r") as f:
            first_message = f.read()
        with open("src/prompts/onboarding/onboarding.md", "r") as f:
            prompt = f.read()
            
        return self.outbound_call(first_message, prompt, None, self.agent_id, self.agent_phone_number_id, self.to_number)
    
    def make_follow_up_call(self):
        with open("src/prompts/follow_up/first_message_follow_up.md", "r") as f:
            first_message = f.read()
        with open("src/prompts/follow_up/follow_up.md", "r") as f:
            prompt = f.read()
            
        context = self.get_last_conversation_context()
        
        return self.outbound_call(first_message, prompt, context, self.agent_id, self.agent_phone_number_id, self.to_number)

if __name__ == "__main__":
    coach_infrastructure = CoachInfrastructure()
    
    required_vars = [
        "AGENT_ID",
        "AGENT_PHONE_NUMBER_ID",
        "TO_NUMBER",
        "ELEVENLABS_API_KEY"
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"Environment variable {var} is not set")
    
    onboarding_call_response = coach_infrastructure.make_onboarding_call()
    coach_infrastructure.last_conversation_id = onboarding_call_response["conversation_id"]
    
    # Wait for user to finish onboarding call
    input("Press Enter to trigger follow-up call...")

    # Make follow-up call
    follow_up_response = coach_infrastructure.make_follow_up_call()
    print("Follow-up call response:", follow_up_response)