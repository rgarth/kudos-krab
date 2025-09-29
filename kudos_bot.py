import os
import logging
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from database import get_db_manager
from config.settings import DEFAULT_PORT
from handlers.help_handler import show_help_message, get_app_mention_message
from handlers.leaderboard_handler import handle_leaderboard_command
from handlers.stats_handler import handle_stats_command
from handlers.kudos_handler import handle_kudos_command
from handlers.config_handler import handle_config_command, handle_config_modal_submission, show_current_config, reset_config_to_defaults, handle_personality_select
from handlers.status_handler import handle_status_command

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Slack app
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Get database manager
db_manager = get_db_manager()


@app.middleware
def log_request(logger, body, next):
    """Log incoming requests for debugging"""
    logger.info(f"🦀 Incoming request: {body.get('type', 'unknown')}")
    if body.get('type') == 'url_verification':
        logger.info(f"🌊 Slack URL verification challenge received: {body.get('challenge', 'no challenge')}")
    return next()


@app.command("/kk")
def handle_kudos_command_wrapper(ack, command, say, respond):
    """Handle the /kk slash command"""
    ack()  # Always acknowledge the command first
    
    user_id = command["user_id"]
    text = command["text"].strip()
    
    # Get channel_id from command
    channel_id = command.get("channel_id")
    
    # Check if it's a dedicated command (first word is a command)
    if text:
        first_word = text.split()[0].lower()
        if first_word == "leaderboard":
            # Parse leaderboard parameters
            leaderboard_params = text[len("leaderboard"):].strip()
            handle_leaderboard_command(respond, db_manager, app, leaderboard_params, channel_id, say)
            return
        elif first_word == "stats":
            handle_stats_command(user_id, respond, db_manager, channel_id)
            return
        elif first_word == "help":
            show_help_message(respond, channel_id, db_manager)
            return
        elif first_word == "config":
            # Handle config command - show current config or open modal
            if len(text.split()) == 1:
                # Just "/kk config" - show current configuration
                show_current_config(respond, channel_id, db_manager)
            elif text.split()[1].lower() == "edit":
                # "/kk config edit" - open configuration modal
                handle_config_command(ack, command, app.client, db_manager)
            elif text.split()[1].lower() == "default":
                # "/kk config default" - reset to defaults
                reset_config_to_defaults(respond, channel_id, db_manager)
            else:
                # "/kk config" with other parameters - show current configuration
                show_current_config(respond, channel_id, db_manager)
            return
        elif first_word == "status":
            handle_status_command(ack, respond, channel_id, db_manager, app.client)
            return
        elif first_word == "version":
            from version import VERSION
            respond(f"📦 *Kudos Krab Version:* {VERSION}")
            return
        elif len(text.split()) == 1:
            # Single word that's not a recognized command - show help
            show_help_message(respond, channel_id, db_manager)
            return
    
    # Handle kudos command
    handle_kudos_command(command, say, respond, app, db_manager)


@app.event("app_mention")
def handle_app_mention(event, say):
    """Handle when the bot is mentioned"""
    channel_id = event.get('channel')
    say(get_app_mention_message(channel_id, db_manager))


@app.action("personality_select")
def handle_personality_select_wrapper(ack, body, client):
    """Handle personality dropdown selection"""
    handle_personality_select(ack, body, client, db_manager)

@app.view("config_modal")
def handle_config_modal_submission_wrapper(ack, body, client):
    """Handle configuration modal submission"""
    handle_config_modal_submission(ack, body, client, db_manager)


# AWS Lambda handler
def lambda_handler(event, context):
    """AWS Lambda handler"""
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)


# For local development
if __name__ == "__main__":
    port = DEFAULT_PORT
    app.start(port=port)
