import click
import os
from coach.coach_infrastructure import CoachInfrastructure
from dotenv import load_dotenv

def check_env_vars():
    required_vars = [
        "AGENT_ID",
        "AGENT_PHONE_NUMBER_ID",
        "TO_NUMBER",
        "ELEVENLABS_API_KEY"
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"Environment variable {var} is not set")

@click.group()
def cli():
    """CLI for managing Her coaching calls."""
    pass

@cli.command()
def onboard():
    """Make an onboarding call."""
    coach = CoachInfrastructure()
    response = coach.make_onboarding_call()
    click.echo(f"Onboarding call initiated. Conversation ID: {response['conversation_id']}")

@cli.command()
def followup():
    """Make a follow-up call using context from the last conversation."""
    coach = CoachInfrastructure()
    response = coach.make_follow_up_call()
    click.echo(f"Follow-up call initiated. New conversation ID: {response['conversation_id']}")

@cli.command()
def transcript():
    """Get the transcript of the last conversation."""
    coach = CoachInfrastructure()
    transcript = coach.get_last_conversation_transcript()
    click.echo(f"Transcript:\n{transcript}")

if __name__ == '__main__':
    cli()