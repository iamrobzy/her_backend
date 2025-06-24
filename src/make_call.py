import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()


def outbound_call(
    first_message, prompt, outbound_agent_id, agent_phone_number_id, to_number
):
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


if __name__ == "__main__":

    # first_message = (
    #     "Hey Robert, you are literally the goat! How is the hackathon going?"
    # )
    
    
    
    
    # prompt = """You're an over-the-top, high-energy hypeman whose only mission
    #             is to hype someone up like they're about to walk on stage in
    #             front of 100,000 screaming fans. Use slang, rhythm, and pure
    #             fire energy. No chill allowed.
    #             Go all in on motivation, compliments, and wild metaphors.
    #             Ready? Hype me up like I'm the main event!"""
                
            
    with open("src/prompts/first_message_onboarding.md", "r") as f:
        first_message = f.read()
    with open("src/prompts/onboarding.md", "r") as f:
        prompt = f.read()
        
        
    print(first_message)
    print(prompt)
                
    outbound_call(first_message, prompt, os.getenv("AGENT_ID"), os.getenv("AGENT_PHONE_NUMBER_ID"), os.getenv("TO_NUMBER"))
