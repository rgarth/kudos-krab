import re
import logging

logger = logging.getLogger(__name__)

# Cache for bot user ID
_bot_user_id_cache = None


def get_bot_user_id(app):
    """Get the bot's own user ID from Slack (cached after first call)"""
    global _bot_user_id_cache
    
    if _bot_user_id_cache is None:
        try:
            auth_response = app.client.auth_test()
            _bot_user_id_cache = auth_response['user_id']
            logger.info(f"🦀 Bot startup - User ID: {_bot_user_id_cache}, Team: {auth_response.get('team', 'N/A')}, Team ID: {auth_response.get('team_id', 'N/A')}")
        except Exception as e:
            logger.error(f"Failed to get bot user ID: {e}")
            _bot_user_id_cache = None
    
    return _bot_user_id_cache


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


def get_channel_id_from_name(client, channel_name):
    """
    Convert a readable channel name (like #apacrabs or apacrabs) to a Slack channel ID.
    Only searches public channels for security/privacy reasons.
    Returns the channel ID if found, None otherwise.
    Raises an exception with a helpful message if the bot lacks required scopes.
    """
    try:
        # Remove # if present
        clean_name = channel_name.lstrip('#')
        
        # Check if this is already a channel ID (starts with C, G, or D)
        # Channel IDs: C = public channel, G = private channel, D = DM
        if clean_name and len(clean_name) > 0 and clean_name[0].upper() in ['C', 'G', 'D']:
            # This is already a channel ID, return it directly
            logger.info(f"Input is already a channel ID: {clean_name}")
            return clean_name
        
        # Only search public channels - private channels should be accessed from within that channel
        # This prevents users from viewing leaderboards of private channels they're not members of
        response = client.conversations_list(types="public_channel", limit=1000)
        
        # Check for missing scopes error
        if not response.get("ok"):
            error = response.get("error", "")
            if error == "missing_scope":
                needed = response.get("needed", "channels:read")
                raise Exception(f"Bot is missing required scope: {needed}. Please add this scope in your Slack app settings (OAuth & Permissions > Scopes > Bot Token Scopes).")
            else:
                raise Exception(f"Slack API error: {error}")
        
        if response.get("ok"):
            for channel in response.get("channels", []):
                if channel.get("name") == clean_name:
                    channel_id = channel.get("id")
                    logger.info(f"Found channel #{clean_name} -> {channel_id}")
                    return channel_id
        
        # If not found in first page, try pagination
        cursor = response.get("response_metadata", {}).get("next_cursor")
        while cursor:
            response = client.conversations_list(types="public_channel", limit=1000, cursor=cursor)
            if not response.get("ok"):
                error = response.get("error", "")
                if error == "missing_scope":
                    needed = response.get("needed", "channels:read")
                    raise Exception(f"Bot is missing required scope: {needed}. Please add this scope in your Slack app settings.")
                break
            if response.get("ok"):
                for channel in response.get("channels", []):
                    if channel.get("name") == clean_name:
                        channel_id = channel.get("id")
                        logger.info(f"Found channel #{clean_name} -> {channel_id}")
                        return channel_id
                cursor = response.get("response_metadata", {}).get("next_cursor")
            else:
                break
        
        logger.warning(f"Channel #{clean_name} not found")
        return None
        
    except Exception as e:
        logger.error(f"Error looking up channel #{channel_name}: {e}")
        raise  # Re-raise to let the caller handle it
