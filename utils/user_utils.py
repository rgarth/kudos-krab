import re
import logging
import time

logger = logging.getLogger(__name__)

# Global cache for username to user ID mapping
_username_cache = {
    'mapping': {}  # username -> user_id
}

def get_username_mapping(app, force_refresh=False):
    """Get username to user ID mapping from cache or fetch from API if needed"""
    global _username_cache
    
    # Return cached mapping if available and not forcing refresh
    if not force_refresh and _username_cache['mapping']:
        logger.info(f"Using cached username mapping ({len(_username_cache['mapping'])} users)")
        return _username_cache['mapping']
    
    # Fetch fresh users from API and build mapping
    try:
        users_response = app.client.users_list()
        users = users_response["members"]
        
        # Build username -> user_id mapping
        mapping = {}
        for user in users:
            username = user.get("name")
            if username:
                mapping[username] = user["id"]
        
        _username_cache['mapping'] = mapping
        logger.info(f"Built and cached username mapping ({len(mapping)} users)")
        return mapping
    except Exception as e:
        logger.error(f"Failed to fetch users: {e}")
        # Return old cache if available, otherwise empty dict
        return _username_cache['mapping'] or {}


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
        
        # Try to find user in cached mapping
        mapping = get_username_mapping(app)
        if mention in mapping:
            user_ids.append(mapping[mention])
            logger.info(f"Found user {mention} via cached mapping: {mapping[mention]}")
            user_found = True
        
        # If not found, refresh cache and try again
        if not user_found:
            logger.info(f"User {mention} not found in cache, refreshing mapping...")
            mapping = get_username_mapping(app, force_refresh=True)
            if mention in mapping:
                user_ids.append(mapping[mention])
                logger.info(f"Found user {mention} after cache refresh: {mapping[mention]}")
                user_found = True
        
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
