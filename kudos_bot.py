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
    """Extract all user IDs from Slack mention format <@U1234567890> from anywhere in the text"""
    matches = re.findall(r'<@([A-Z0-9]+)>', text)
    return matches

def extract_message_text(text):
    """Extract the message text after removing all user mentions"""
    # Remove all user mentions and clean up the text
    cleaned_text = re.sub(r'<@[A-Z0-9]+>\s*', '', text).strip()
    return cleaned_text

def show_help_message(say):
    """Show the help message with all available commands"""
    help_text = """HEY THERE, BUDDY! 🦀 Here's how to make some waves, fella:

*🎯 Send Kudos:*
• `/kk @user message` - Send love to one person
• `/kk @user1 @user2 message` - Spread the love to multiple people
• `/kk Thanks @user for the help!` - Free-form messages work too!

*📊 Commands:*
• `/kk leaderboard` - See who's making the biggest splash this month
• `/kk stats` - Check your own kudos journey
• `/kk help` - Show this help message

*💡 Examples:*
• `/kk @alice thanks for the awesome help!`
• `/kk @bob @charlie you both crushed that project!`
• `/kk Great work @david on the presentation yesterday`

Now go make some magic, bud! 🌊✨"""
    say(help_text)

def format_leaderboard(leaderboard_data, month, year):
    """Format leaderboard data for Slack message"""
    month_name = datetime(year, month, 1).strftime("%B %Y")
    
    # Format top senders
    senders_text = "*🏆 TOP KUDOS SPREADERS 🏆*\n"
    if leaderboard_data['senders']:
        for i, (sender, count) in enumerate(leaderboard_data['senders'], 1):
            senders_text += f"{i}. <@{sender}> - {count} kudos 🌊\n"
    else:
        senders_text += "No kudos sent this month yet! Let's get this party started! 🦀\n"
    
    # Format top receivers
    receivers_text = "\n*🌟 TOP KUDOS RECEIVERS 🌟*\n"
    if leaderboard_data['receivers']:
        for i, (receiver, count) in enumerate(leaderboard_data['receivers'], 1):
            receivers_text += f"{i}. <@{receiver}> - {count} kudos 🐚\n"
    else:
        receivers_text += "No kudos received this month yet! Time to spread some love! 🌊\n"
    
    return f"*🦀 {month_name} KUDOS CHAMPIONS 🦀*\n\n{senders_text}{receivers_text}\n\n*Keep making those waves!* 🌊✨"

@app.command("/kk")
def handle_kudos_command(ack, command, say):
    """Handle the /kk slash command"""
    ack()
    
    user_id = command["user_id"]
    text = command["text"].strip()
    
    # Check if it's a dedicated command (first word is a command)
    if text:
        first_word = text.split()[0].lower()
        if first_word == "leaderboard":
            handle_leaderboard_command(say)
            return
        elif first_word == "stats":
            handle_stats_command(user_id, say)
            return
        elif first_word == "help":
            show_help_message(say)
            return
        elif len(text.split()) == 1:
            # Single word that's not a recognized command - show help
            show_help_message(say)
            return
    
    # Parse kudos command: anything else is treated as a kudos message
    if not text:
        show_help_message(say)
        return
    
    # Extract all mentioned users
    mentioned_users = extract_user_mentions(text)
    if not mentioned_users:
        say("HEY THERE, BUD! 🦀 You gotta mention someone with @username to send them some love! 🌊 Don't be shy, fella - spread those good vibes! ✨\n\nTry `/kk help` to see how to use the bot!")
        return
    
    # Remove duplicates while preserving order
    unique_users = []
    for user in mentioned_users:
        if user not in unique_users:
            unique_users.append(user)
    
    # Check if user is trying to send kudos to themselves
    if user_id in unique_users:
        say("NICE TRY, BUDDY! 😂 But you can't give yourself kudos, you silly crab! 🦀 Save that self-love for someone else, fella! 🌊✨ Maybe try giving yourself a high-five instead? 🤚")
        return
    
    # Check if user is trying to send kudos to the bot
    bot_user_id = os.environ.get("SLACK_BOT_USER_ID")
    if bot_user_id and bot_user_id in unique_users:
        say("AWWW, BUDDY! 🥺 You're trying to give ME kudos? That's so sweet! 🦀 *blushes in crab* 🌊✨ But I'm just here to help spread the love - save those kudos for your amazing teammates! 💕 Maybe try `/kk help` to see how to send kudos to others? 🦀")
        return
    
    # Extract message
    message = extract_message_text(text)
    if not message:
        say("COME ON, BUD! 🦀 You can't just send empty kudos! 🌊 Add some words to make it special, fella - that's what makes the ocean sparkle! ✨")
        return
    
    # Check monthly quota for multiple kudos
    current_month = datetime.now().month
    current_year = datetime.now().year
    monthly_count = db_manager.get_monthly_kudos_count(user_id, current_month, current_year)
    kudos_needed = len(unique_users)
    
    if monthly_count + kudos_needed > MONTHLY_QUOTA:
        say(f"YIKES, BUDDY! 😅 Looks like you're all out of kudos juice! 🦀 You need {kudos_needed} more but only have {MONTHLY_QUOTA - monthly_count} left this month, fella. Time to wait for the next tide to roll in! 🌊")
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
            announcement = f"🦀 *OH SNAP!* 🦀\n<@{user_id}> just dropped some MAJOR kudos on <@{successful_kudos[0]}>! 🌊\n\n> {message}\n\n*That's what I'm talking about!* 🦀✨"
        else:
            user_mentions = " ".join([f"<@{user}>" for user in successful_kudos])
            announcement = f"🦀 *HOLY CRAB!* 🦀\n<@{user_id}> just went FULL OCEAN MODE and sent kudos to {user_mentions}! 🌊🐚\n\n> {message}\n\n*Now THAT'S how you make waves!* 🦀✨"
        
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
            say(f"BOOM, BUDDY! 💥 Kudos delivered like a tidal wave! 🦀 You've got {remaining} more kudos left this month, fella - keep that energy flowing! 🌊✨")
        else:
            say(f"WHOA, BUD! 🚀 You just made it RAIN kudos on {len(successful_kudos)} people! 🦀 That's {remaining} more kudos in your tank, fella - you're on FIRE! 🔥🌊")
    
    if failed_kudos:
        failed_mentions = " ".join([f"<@{user}>" for user in failed_kudos])
        say(f"OOPS, BUDDY! 😅 Looks like the ocean got a bit choppy for {failed_mentions}! 🦀 Let's try that again, fella - the tide will be better this time! 🌊")

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
        say("YIKES, BUDDY! 😅 The ocean got a bit rough while I was checking the leaderboard! 🦀 Let's try that again, fella - the waves should be calmer now! 🌊")

def handle_stats_command(user_id, say):
    """Handle stats request"""
    try:
        stats = db_manager.get_user_stats(user_id)
        current_month = datetime.now().month
        current_year = datetime.now().year
        monthly_count = db_manager.get_monthly_kudos_count(user_id, current_month, current_year)
        
        stats_message = f"""🦀 *YOUR KUDOS JOURNEY* 🦀

*Total Kudos Sent:* {stats['total_sent']} 🌊
*Total Kudos Received:* {stats['total_received']} 🐚
*Kudos Sent This Month:* {stats['monthly_sent']} 🚀
*Remaining This Month:* {MONTHLY_QUOTA - monthly_count} ✨

*You're absolutely CRUSHING it!* 🔥"""
        
        say(stats_message)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        say("OOPS, BUDDY! 😅 The ocean got a bit murky while I was checking your stats! 🦀 Let's try that again, fella - the water should be clearer now! 🌊")

@app.event("app_mention")
def handle_app_mention(event, say):
    """Handle when the bot is mentioned"""
    say("HEY THERE, BUDDY! 🦀 I'm your favorite kudos coach! 🌊\n\nHere's how to make some waves, fella:\n• `/kk @user message` - Send love to one person\n• `/kk @user1 @user2 message` - Spread the love to multiple people\n• `/kk leaderboard` - See who's making the biggest splash\n• `/kk stats` - Check your own kudos journey\n\nLet's make this ocean sparkle, bud! ✨")

# AWS Lambda handler
def lambda_handler(event, context):
    """AWS Lambda handler"""
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)

# For local development
if __name__ == "__main__":
    app.start(port=3000) 