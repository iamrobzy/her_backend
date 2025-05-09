import os
import requests
import json
from dotenv import load_dotenv
load_dotenv() 


def outbound_call(first_message, prompt):
    curl_url = "https://api.elevenlabs.io/v1/convai/twilio/outbound_call"
    curl_headers = {
        "Xi-Api-Key": os.getenv("ELEVENLABS_API_KEY"),
        "Content-Type": "application/json",
    }

    curl_data = {
        "agent_id": os.getenv("AGENT_ID"),
        "agent_phone_number_id": os.getenv("AGENT_PHONE_NUMBER_ID"),
        "to_number": os.getenv("TO_NUMBER"),
        "conversation_initiation_client_data": {
            "conversation_config_override": {
                "agent": {
                    "prompt": {
                        "prompt": prompt
                    },
                    "first_message": first_message
                }
            }
        }
    }

    curl_response = requests.post(curl_url, headers=curl_headers, data=json.dumps(curl_data))
    return curl_response.json()

if __name__ == "__main__":

    first_message = "Hey Robert, you are literally the goat! How is the hackathon going?"
    prompt = "You're an over-the-top, high-energy hypeman whose only mission is to hype someone up like they're about to walk on stage in front of 100,000 screaming fans. Use slang, rhythm, and pure fire energy. No chill allowed. Go all in on motivation, compliments, and wild metaphors. Ready? Hype me up like I'm the main event!"
    outbound_call(first_message, prompt)