import re
import logging

logger = logging.getLogger(__name__)


def extract_user_mentions(text):
    """Extract all user IDs from Slack mention format <@U1234567890> or @username from anywhere in the text"""
    logger.info(f"Extracting mentions from text: '{text}'")
    
    # First try to find Slack mention format <@U1234567890>
    matches = re.findall(r'<@([A-Z0-9]+)>', text)
    if matches:
        logger.info(f"Found Slack mention format: {matches}")
        return matches
    
    # If no matches, look for @username format (for slash commands)
    username_matches = re.findall(r'@([a-zA-Z0-9_]+)', text)
    # Filter out common Slack keywords
    filtered_matches = [match for match in username_matches if match.lower() not in ['channel', 'here', 'everyone']]
    
    logger.info(f"Found @username format: {filtered_matches}")
    return filtered_matches


def extract_message_text(text):
    """Extract the message text - keep original message intact"""
    # Just return the original text, don't strip usernames
    return text.strip()


def convert_usernames_to_user_ids(app, mentioned_users):
    """Convert usernames to user IDs"""
    user_ids = []
    for mention in mentioned_users:
        # Username, need to look up user ID
        user_found = False
        
        # Method 1: Try users.list to find by username (primary method)
        try:
            users_response = app.client.users_list()
            for user in users_response["members"]:
                if user.get("name") == mention:
                    user_ids.append(user["id"])
                    logger.info(f"Found user {mention} via users.list: {user['id']}")
                    user_found = True
                    break
        except Exception as list_error:
            logger.error(f"Users list lookup failed for {mention}: {list_error}")
        
        # Method 2: Try users.lookupByEmail as fallback (for Enterprise workspaces)
        if not user_found:
            try:
                user_info = app.client.users_lookupByEmail(email=f"{mention}@slack.com")
                user_ids.append(user_info["user"]["id"])
                logger.info(f"Found user {mention} via email lookup: {user_info['user']['id']}")
                user_found = True
            except Exception as email_error:
                logger.info(f"Email lookup failed for {mention}: {email_error}")
        
        if not user_found:
            raise Exception(f"Could not find user with username @{mention}. Make sure the username is correct and the user is in this workspace.")
    
    return user_ids


def remove_duplicate_users(user_list):
    """Remove duplicates while preserving order"""
    unique_users = []
    for user in user_list:
        if user not in unique_users:
            unique_users.append(user)
    return unique_users


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
