import os
import re
import logging
from datetime import datetime
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from database import get_db_manager

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

# Configuration
MONTHLY_QUOTA = int(os.environ.get("MONTHLY_QUOTA", "10"))
SLACK_CHANNEL_ID = os.environ.get("SLACK_CHANNEL_ID")

def extract_user_mentions(text):
    """Extract all user IDs from Slack mention format <@U1234567890>"""
    matches = re.findall(r'<@([A-Z0-9]+)>', text)
    return matches

def extract_message_text(text):
    """Extract the message text after removing all user mentions"""
    # Remove all user mentions and clean up the text
    cleaned_text = re.sub(r'<@[A-Z0-9]+>\s*', '', text).strip()
    return cleaned_text

def format_leaderboard(leaderboard_data, month, year):
    """Format leaderboard data for Slack message"""
    month_name = datetime(year, month, 1).strftime("%B %Y")
    
    # Format top senders
    senders_text = "*Top Kudos Senders:*\n"
    if leaderboard_data['senders']:
        for i, (sender, count) in enumerate(leaderboard_data['senders'], 1):
            senders_text += f"{i}. <@{sender}> - {count} kudos\n"
    else:
        senders_text += "No kudos sent this month yet!\n"
    
    # Format top receivers
    receivers_text = "\n*Top Kudos Receivers:*\n"
    if leaderboard_data['receivers']:
        for i, (receiver, count) in enumerate(leaderboard_data['receivers'], 1):
            receivers_text += f"{i}. <@{receiver}> - {count} kudos\n"
    else:
        receivers_text += "No kudos received this month yet!\n"
    
    return f"*🦀 {month_name} Kudos Leaderboard 🦀*\n\n{senders_text}{receivers_text}"

@app.command("/kk")
def handle_kudos_command(ack, command, say):
    """Handle the /kk slash command"""
    ack()
    
    user_id = command["user_id"]
    text = command["text"].strip()
    
    # Check if it's a command (starts with a word that's not a mention)
    if text and not text.startswith('<@'):
        first_word = text.split()[0].lower()
        if first_word == "leaderboard":
            handle_leaderboard_command(say)
            return
        elif first_word == "stats":
            handle_stats_command(user_id, say)
            return
    
    # Parse kudos command: /kk @user1 @user2 message
    if not text:
        say("Usage: `/kk @user message` or `/kk @user1 @user2 message` or `/kk leaderboard` or `/kk stats`")
        return
    
    # Extract all mentioned users
    mentioned_users = extract_user_mentions(text)
    if not mentioned_users:
        say("Please mention at least one user with @username to send kudos!")
        return
    
    # Remove duplicates while preserving order
    unique_users = []
    for user in mentioned_users:
        if user not in unique_users:
            unique_users.append(user)
    
    # Check if user is trying to send kudos to themselves
    if user_id in unique_users:
        say("You can't send kudos to yourself! 🦀")
        return
    
    # Extract message
    message = extract_message_text(text)
    if not message:
        say("Please include a message with your kudos!")
        return
    
    # Check monthly quota for multiple kudos
    current_month = datetime.now().month
    current_year = datetime.now().year
    monthly_count = db_manager.get_monthly_kudos_count(user_id, current_month, current_year)
    kudos_needed = len(unique_users)
    
    if monthly_count + kudos_needed > MONTHLY_QUOTA:
        say(f"You don't have enough kudos remaining! You need {kudos_needed} kudos but only have {MONTHLY_QUOTA - monthly_count} remaining this month. 🦀")
        return
    
    # Record kudos for each user
    successful_kudos = []
    failed_kudos = []
    
    for receiver in unique_users:
        if db_manager.record_kudos(user_id, receiver, message):
            successful_kudos.append(receiver)
        else:
            failed_kudos.append(receiver)
    
    # Send announcements and confirm
    if successful_kudos:
        # Send announcement to channel
        if len(successful_kudos) == 1:
            announcement = f"🦀 *Kudos Alert!* 🦀\n<@{user_id}> just sent kudos to <@{successful_kudos[0]}>:\n\n> {message}"
        else:
            user_mentions = " ".join([f"<@{user}>" for user in successful_kudos])
            announcement = f"🦀 *Kudos Alert!* 🦀\n<@{user_id}> just sent kudos to {user_mentions}:\n\n> {message}"
        
        if SLACK_CHANNEL_ID:
            try:
                app.client.chat_postMessage(
                    channel=SLACK_CHANNEL_ID,
                    text=announcement,
                    unfurl_links=False
                )
            except Exception as e:
                logger.error(f"Failed to post to channel: {e}")
        
        # Confirm to user
        remaining = MONTHLY_QUOTA - monthly_count - len(successful_kudos)
        if len(successful_kudos) == 1:
            say(f"Kudos sent! 🦀 You have {remaining} kudos remaining this month.")
        else:
            say(f"Kudos sent to {len(successful_kudos)} people! 🦀 You have {remaining} kudos remaining this month.")
    
    if failed_kudos:
        failed_mentions = " ".join([f"<@{user}>" for user in failed_kudos])
        say(f"Failed to send kudos to: {failed_mentions}. Please try again!")

def handle_leaderboard_command(say):
    """Handle leaderboard request"""
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    try:
        leaderboard_data = db_manager.get_monthly_leaderboard(current_month, current_year)
        formatted_leaderboard = format_leaderboard(leaderboard_data, current_month, current_year)
        say(formatted_leaderboard)
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        say("Sorry, there was an error getting the leaderboard. Please try again!")

def handle_stats_command(user_id, say):
    """Handle stats request"""
    try:
        stats = db_manager.get_user_stats(user_id)
        current_month = datetime.now().month
        current_year = datetime.now().year
        monthly_count = db_manager.get_monthly_kudos_count(user_id, current_month, current_year)
        
        stats_message = f"""🦀 *Your Kudos Stats* 🦀

*Total Kudos Sent:* {stats['total_sent']}
*Total Kudos Received:* {stats['total_received']}
*Kudos Sent This Month:* {stats['monthly_sent']}
*Remaining This Month:* {MONTHLY_QUOTA - monthly_count}"""
        
        say(stats_message)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        say("Sorry, there was an error getting your stats. Please try again!")

@app.event("app_mention")
def handle_app_mention(event, say):
    """Handle when the bot is mentioned"""
    say("Hi! I'm Kudos Krab 🦀 Use `/kk @user message` to send kudos, `/kk @user1 @user2 message` to send to multiple people, `/kk leaderboard` to see the monthly leaderboard, or `/kk stats` to see your stats!")

# AWS Lambda handler
def lambda_handler(event, context):
    """AWS Lambda handler"""
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)

# For local development
if __name__ == "__main__":
    app.start(port=3000) 