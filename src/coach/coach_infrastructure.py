import os
import json
import requests
from zep_cloud import Zep
from dotenv import load_dotenv

class CoachInfrastructure:
    def __init__(self):
        load_dotenv()
        self.zep_client = Zep(
            api_key=os.getenv("ZEP_API_KEY")
        )
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        self.agent_id = os.getenv("AGENT_ID")
        self.agent_phone_number_id = os.getenv("AGENT_PHONE_NUMBER_ID")
        self.to_number = os.getenv("TO_NUMBER")

    def outbound_call(first_message, prompt, outbound_agent_id, agent_phone_number_id, to_number):
        curl_url = "https://api.elevenlabs.io/v1/convai/twilio/outbound_call"
        curl_headers = {
            "Xi-Api-Key": os.getenv("ELEVENLABS_API_KEY"),
            "Content-Type": "application/json",
        }

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
    
    def make_outbound_call(self):
        with open("src/prompts/first_message_onboarding.md", "r") as f:
            first_message = f.read()
        with open("src/prompts/onboarding.md", "r") as f:
            prompt = f.read()
            
        return self.outbound_call(first_message, prompt, self.agent_id, self.agent_phone_number_id, self.to_number)

if __name__ == "__main__":
    coach_infrastructure = CoachInfrastructure()
    
    required_vars = [
        "AGENT_ID",
        "AGENT_PHONE_NUMBER_ID",
        "TO_NUMBER",
        "ZEP_API_KEY",
        "ELEVENLABS_API_KEY"
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"Environment variable {var} is not set")
    
    outbound_call_response = coach_infrastructure.make_outbound_call()
    
    print(outbound_call_response)
    
    