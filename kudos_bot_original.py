import os
import re
import logging
from datetime import datetime, date
from calendar import month_name, month_abbr
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

def parse_month_year(text):
    """Parse month and year from text input"""
    if not text:
        return None, None
    
    text = text.strip().lower()
    parts = text.split()
    
    # Initialize variables
    month = None
    year = None
    
    # Create month mappings
    month_map = {}
    for i in range(1, 13):
        # Full month names
        month_map[month_name[i].lower()] = i
        # Three letter abbreviations
        month_map[month_abbr[i].lower()] = i
        # Numeric months
        month_map[str(i)] = i
        month_map[f"{i:02d}"] = i
    
    # Parse parts
    for part in parts:
        part = part.strip()
        
        # Check if it's a month
        if part in month_map:
            month = month_map[part]
        # Check if it's a year (4 digits)
        elif re.match(r'^\d{4}$', part):
            year = int(part)
        # Check if it's a 2-digit year (assume 20xx)
        elif re.match(r'^\d{2}$', part):
            year = 2000 + int(part)
    
    return month, year

def get_target_date(month, year):
    """Get the target date for the leaderboard"""
    today = date.today()
    
    if month is None and year is None:
        # Default to current month
        return today.month, today.year
    
    if month is None:
        # Year specified but no month - use current month
        month = today.month
    
    if year is None:
        # Month specified but no year - find the most recent occurrence
        target_year = today.year
        target_date = date(target_year, month, 1)
        
        # If this month hasn't happened yet this year, go back to last year
        if target_date > today:
            target_year = today.year - 1
        
        return month, target_year
    
    return month, year

@app.middleware
def log_request(logger, body, next):
    """Log incoming requests for debugging"""
    logger.info(f"🦀 Incoming request: {body.get('type', 'unknown')}")
    if body.get('type') == 'url_verification':
        logger.info(f"🌊 Slack URL verification challenge received: {body.get('challenge', 'no challenge')}")
    return next()



def extract_user_mentions(text):
    """Extract all user IDs from Slack mention format <@U1234567890> or @username from anywhere in the text"""
    # First try to find Slack mention format <@U1234567890>
    matches = re.findall(r'<@([A-Z0-9]+)>', text)
    
    # If no matches, look for @username format (for slash commands)
    if not matches:
        # Find @username patterns (but not @channel, @here, etc.)
        username_matches = re.findall(r'@([a-zA-Z0-9_]+)', text)
        # Filter out common Slack keywords
        filtered_matches = [match for match in username_matches if match.lower() not in ['channel', 'here', 'everyone']]
        matches = filtered_matches
    
    return matches

def extract_message_text(text):
    """Extract the message text - keep original message intact"""
    # Just return the original text, don't strip usernames
    return text.strip()

def show_help_message(respond):
    """Show the help message with all available commands"""
    help_text = """HEY THERE, BUDDY! 🦀 Here's how to make some waves:

*🎯 Send Kudos:*
• `/kk @user message` - Send love to one person
• `/kk @user1 @user2 message` - Spread the love to multiple people
• `/kk Thanks @user for the help!` - Free-form messages work too!

*📊 Commands:*
• `/kk leaderboard` - See who's making the biggest splash this month
• `/kk leaderboard Aug|08 [2025]` - See August leaderboard (year is optional)
• `/kk stats` - Check your own kudos journey
• `/kk help` - Show this help message

Now go make some magic, bud! 🌊✨"""
    respond(help_text)

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
def handle_kudos_command(ack, command, say, respond):
    """Handle the /kk slash command"""
    ack()
    
    user_id = command["user_id"]
    text = command["text"].strip()
    
    # Check if it's a dedicated command (first word is a command)
    if text:
        first_word = text.split()[0].lower()
        if first_word == "leaderboard":
            # Parse leaderboard parameters
            leaderboard_params = text[len("leaderboard"):].strip()
            handle_leaderboard_command(respond, leaderboard_params)
            return
        elif first_word == "stats":
            handle_stats_command(user_id, respond)
            return
        elif first_word == "help":
            show_help_message(respond)
            return
        elif len(text.split()) == 1:
            # Single word that's not a recognized command - show help
            show_help_message(respond)
            return
    
    # Parse kudos command: anything else is treated as a kudos message
    if not text:
        show_help_message(respond)
        return
    
    # Extract all mentioned users
    mentioned_users = extract_user_mentions(text)
    
    # Debug: Log what we received
    logger.info(f"Received text: '{text}'")
    logger.info(f"Extracted mentions: {mentioned_users}")
    
    if not mentioned_users:
        respond("HEY THERE, BUD! 🦀 You gotta mention someone with @username to send them some love! 🌊 Don't be shy, dude - spread those good vibes! ✨\n\nTry `/kk help` to see how to use the bot!")
        return
    
    # Convert usernames to user IDs - REQUIRED since usernames can change
    user_ids = []
    for mention in mentioned_users:
        # Username, need to look up user ID
        try:
            # Try to get user by username
            user_info = app.client.users_lookupByEmail(email=f"{mention}@slack.com")
            user_ids.append(user_info["user"]["id"])
        except:
            # Try alternative lookup methods
            try:
                # Try users.list to find by username
                users_response = app.client.users_list()
                for user in users_response["members"]:
                    if user.get("name") == mention:
                        user_ids.append(user["id"])
                        break
                else:
                    raise Exception("User not found")
            except:
                respond(f"OOPS, BUDDY! 😅 I couldn't find a user with username @{mention}! 🦀 Make sure you're using the correct username, friend! 🌊")
                return
    
    mentioned_users = user_ids
    
    # Remove duplicates while preserving order
    unique_users = []
    for user in mentioned_users:
        if user not in unique_users:
            unique_users.append(user)
    
    # Check if user is trying to send kudos to themselves
    if user_id in unique_users:
        respond("NICE TRY, BUDDY! 😂 But you can't give yourself kudos, you silly crab! 🦀 Save that self-love for someone else, friend! 🌊✨ Maybe try giving yourself a high-five instead? 🤚")
        return
    
    # Check if user is trying to send kudos to the bot
    bot_user_id = os.environ.get("SLACK_BOT_USER_ID")
    if bot_user_id and bot_user_id in unique_users:
        respond("AWWW, BUDDY! 🥺 You're trying to give ME kudos? That's so sweet! 🦀 *blushes in crab* 🌊✨ But I'm just here to help spread the love - save those kudos for your amazing teammates! 💕 Maybe try `/kk help` to see how to send kudos to others? 🦀")
        return
    
    # Extract message
    message = extract_message_text(text)
    if not message:
        respond("COME ON, BUD! 🦀 You can't just send empty kudos! 🌊 Add some words to make it special, friend - that's what makes the ocean sparkle! ✨")
        return
    
    # Check monthly quota for multiple kudos
    current_month = datetime.now().month
    current_year = datetime.now().year
    monthly_count = db_manager.get_monthly_kudos_count(user_id, current_month, current_year)
    kudos_needed = len(unique_users)
    
    if monthly_count + kudos_needed > MONTHLY_QUOTA:
        respond(f"YIKES, BUDDY! 😅 Looks like you're all out of kudos juice! 🦀 You need {kudos_needed} more but only have {MONTHLY_QUOTA - monthly_count} left this month, friend. Time to wait for the next tide to roll in! 🌊")
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
            respond(f"BOOM, BUDDY! 💥 Kudos delivered like a tidal wave! 🦀 You've got {remaining} more kudos left this month, friend - keep that energy flowing! 🌊✨")
        else:
            respond(f"WHOA, BUD! 🚀 You just made it RAIN kudos on {len(successful_kudos)} people! 🦀 That's {remaining} more kudos in your tank, friend - you're on FIRE! 🔥🌊")
    
    if failed_kudos:
        failed_mentions = " ".join([f"<@{user}>" for user in failed_kudos])
        respond(f"OOPS, BUDDY! 😅 Looks like the ocean got a bit choppy for {failed_mentions}! 🦀 Let's try that again, friend - the tide will be better this time! 🌊")

def handle_leaderboard_command(respond, params=""):
    """Handle leaderboard request with optional month/year parameters"""
    try:
        # Parse month and year from parameters
        month, year = parse_month_year(params)
        target_month, target_year = get_target_date(month, year)
        
        # Log the parsing results for debugging
        logger.info(f"Leaderboard request - params: '{params}', parsed: month={month}, year={year}, target: {target_month}/{target_year}")
        
        # Get leaderboard data
        leaderboard_data = db_manager.get_monthly_leaderboard(target_month, target_year)
        formatted_leaderboard = format_leaderboard(leaderboard_data, target_month, target_year)
        respond(formatted_leaderboard)
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        respond("YIKES, BUDDY! 😅 The ocean got a bit rough while I was checking the leaderboard! 🦀 Let's try that again, friend - the waves should be calmer now! 🌊")

def handle_stats_command(user_id, respond):
    """Handle stats request"""
    try:
        current_month = datetime.now().month
        current_year = datetime.now().year
        monthly_sent = db_manager.get_monthly_kudos_count(user_id, current_month, current_year)
        monthly_received = db_manager.get_monthly_kudos_received_count(user_id, current_month, current_year)
        
        stats_message = f"""🦀 *YOUR MONTHLY KUDOS STATUS* 🦀

*This Month:*
• Kudos Sent: {monthly_sent} 🌊
• Kudos Received: {monthly_received} 🐚
• Remaining to Send: {MONTHLY_QUOTA - monthly_sent} ✨

*All Time:*
• Total Kudos Sent: {db_manager.get_user_stats(user_id)['total_sent']} 🚀
• Total Kudos Received: {db_manager.get_user_stats(user_id)['total_received']} 💎

*You're absolutely CRUSHING it!* 🔥"""
        
        respond(stats_message)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        respond("OOPS, BUDDY! 😅 The ocean got a bit murky while I was checking your stats! 🦀 Let's try that again, friend - the water should be clearer now! 🌊")

@app.event("app_mention")
def handle_app_mention(event, say):
    """Handle when the bot is mentioned"""
    say("HEY THERE, BUDDY! 🦀 I'm your favorite kudos coach! 🌊\n\nHere's how to make some waves:\n• `/kk @user message` - Send love to one person\n• `/kk @user1 @user2 message` - Spread the love to multiple people\n• `/kk leaderboard` - See who's making the biggest splash\n• `/kk leaderboard Aug 2025` - See specific month/year\n• `/kk stats` - Check your own kudos journey\n\nLet's make this ocean sparkle, bud! ✨")

# AWS Lambda handler
def lambda_handler(event, context):
    """AWS Lambda handler"""
    slack_handler = SlackRequestHandler(app=app)
    return slack_handler.handle(event, context)

# For local development
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "3000"))
    app.start(port=port) 