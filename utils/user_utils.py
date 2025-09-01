import re
import logging

logger = logging.getLogger(__name__)


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


def convert_usernames_to_user_ids(app, mentioned_users):
    """Convert usernames to user IDs"""
    user_ids = []
    for mention in mentioned_users:
        # Username, need to look up user ID
        user_found = False
        
        # Method 1: Try users.lookupByEmail (for Enterprise workspaces)
        try:
            user_info = app.client.users_lookupByEmail(email=f"{mention}@slack.com")
            user_ids.append(user_info["user"]["id"])
            logger.info(f"Found user {mention} via email lookup: {user_info['user']['id']}")
            user_found = True
        except Exception as email_error:
            logger.info(f"Email lookup failed for {mention}: {email_error}")
        
        # Method 2: Try users.list to find by username (fallback method)
        if not user_found:
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
        
        # Method 3: Try with different email domains (common Enterprise patterns)
        if not user_found:
            common_domains = ["company.com", "enterprise.com", "corp.com", "org.com"]
            for domain in common_domains:
                try:
                    user_info = app.client.users_lookupByEmail(email=f"{mention}@{domain}")
                    user_ids.append(user_info["user"]["id"])
                    logger.info(f"Found user {mention} via {domain} lookup: {user_info['user']['id']}")
                    user_found = True
                    break
                except Exception:
                    continue
        
        if not user_found:
            raise Exception(f"Could not find user with username @{mention}. In Enterprise workspaces, try using their full email address or check that they're in this workspace.")
    
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
