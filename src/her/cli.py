import asyncio, click
import os
from her.engine.coach_infrastructure import CoachInfrastructure
from dotenv import load_dotenv
from her.services.conversation_service import ConversationService
from her.platform.settings import settings
from her.platform.db import Session
from her.platform.db.models import User, Conversation

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

@cli.command()
@click.argument("user_id")
@click.option("--phone", "-p", prompt=True)
def adduser(user_id, phone):
    from her.platform.db import Session
    from her.platform.db.models import User
    with Session() as db:
        db.add(User(id=user_id, phone=phone))
        db.commit()
    click.echo("User added.")

@cli.command()
@click.argument("user_id")
@click.option("--flow", "-f", default="onboarding")
def call(user_id, flow):
    service = ConversationService("phone")
    conv_id = asyncio.run(service.trigger(user_id, flow))
    click.echo(f"Started conversation {conv_id}")

@cli.command()
@click.argument("user_id")
def history(user_id):
    """Show conversation history for a user."""
    with Session() as db:
        user = db.get(User, user_id)
        if not user:
            click.echo(f"No user found with id '{user_id}'")
            return
        
        convos = db.query(Conversation)\
                  .filter(Conversation.user_id == user_id)\
                  .order_by(Conversation.started.desc())\
                  .all()
        
        if not convos:
            click.echo(f"No conversations found for user '{user_id}'")
            return
            
        click.echo(f"\nConversations for {user_id}:")
        for conv in convos:
            click.echo(f"\n[{conv.started}] {conv.flow} call (ID: {conv.id})")
            if conv.transcript:
                click.echo(f"Transcript: {conv.transcript[:200]}...")
            else:
                click.echo("No transcript available")

if __name__ == '__main__':
    cli()