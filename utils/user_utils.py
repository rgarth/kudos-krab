import re
import logging

logger = logging.getLogger(__name__)


def extract_user_mentions(text):
    """Extract all user IDs from Slack mention format <@U1234567890> or <@U1234567890|display_name>"""
    logger.info(f"Extracting mentions from text: '{text}'")
    
    # Find Slack mention format <@U1234567890> or <@U1234567890|display_name>
    matches = re.findall(r'<@([A-Z0-9]+)(?:\|[^>]*)?>', text)
    logger.info(f"Found user IDs: {matches}")
    return matches


def extract_message_text(text):
    """Extract the message text - keep original message intact"""
    # Just return the original text, don't strip usernames
    return text.strip()


def remove_duplicate_users(user_list):
    """Remove duplicates while preserving order"""
    unique_users = []
    for user in user_list:
        if user not in unique_users:
            unique_users.append(user)
    return unique_users


def get_bot_user_id(app):
    """Get the bot's own user ID from Slack"""
    try:
        auth_response = app.client.auth_test()
        return auth_response['user_id']
    except Exception as e:
        logger.error(f"Failed to get bot user ID: {e}")
        return None

def validate_kudos_recipients(user_id, unique_users, bot_user_id):
    """Validate kudos recipients and return validation errors"""
    errors = []
    
    # Check if user is trying to send kudos to themselves
    if user_id in unique_users:
        errors.append("self_kudos")
    
    # Check if user is trying to send kudos to the bot
    if bot_user_id and bot_user_id in unique_users:
        errors.append("bot_kudos")
    
    return errors
