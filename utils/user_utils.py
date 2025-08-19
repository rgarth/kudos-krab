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
                raise Exception(f"Could not find user with username @{mention}")
    
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
