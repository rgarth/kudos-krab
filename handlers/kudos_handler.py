import logging
from datetime import datetime
from config.settings import MONTHLY_QUOTA, SLACK_CHANNEL_ID, SLACK_BOT_USER_ID
from utils.user_utils import (
    extract_user_mentions, 
    extract_message_text, 
    convert_usernames_to_user_ids,
    remove_duplicate_users,
    validate_kudos_recipients
)
from utils.message_formatter import (
    format_kudos_announcement,
    format_kudos_confirmation,
    format_error_message
)

logger = logging.getLogger(__name__)


def handle_kudos_command(command, say, respond, app, db_manager):
    """Handle the /kk slash command"""
    user_id = command["user_id"]
    text = command["text"].strip()
    
    # Parse kudos command: anything else is treated as a kudos message
    if not text:
        respond(format_error_message("no_mentions"))
        return True
    
    # Extract all mentioned users
    mentioned_users = extract_user_mentions(text)
    
    # Debug: Log what we received
    logger.info(f"Received text: '{text}'")
    logger.info(f"Extracted mentions: {mentioned_users}")
    
    if not mentioned_users:
        respond(format_error_message("no_mentions"))
        return True
    
    # Convert usernames to user IDs
    try:
        user_ids = convert_usernames_to_user_ids(app, mentioned_users)
    except Exception as e:
        username = mentioned_users[0] if mentioned_users else "unknown"
        respond(format_error_message("user_not_found", username=username))
        return True
    
    # Remove duplicates while preserving order
    unique_users = remove_duplicate_users(user_ids)
    
    # Validate recipients
    logger.info(f"Validating recipients - user_id: {user_id}, unique_users: {unique_users}, bot_user_id: {SLACK_BOT_USER_ID}")
    validation_errors = validate_kudos_recipients(user_id, unique_users, SLACK_BOT_USER_ID)
    logger.info(f"Validation errors: {validation_errors}")
    
    if "self_kudos" in validation_errors:
        respond(format_error_message("self_kudos"))
        return True
    
    if "bot_kudos" in validation_errors:
        respond(format_error_message("bot_kudos"))
        return True
    
    # Extract message
    message = extract_message_text(text)
    if not message:
        respond(format_error_message("empty_message"))
        return True
    
    # Check monthly quota for multiple kudos
    current_month = datetime.now().month
    current_year = datetime.now().year
    monthly_count = db_manager.get_monthly_kudos_count(user_id, current_month, current_year)
    kudos_needed = len(unique_users)
    
    if monthly_count + kudos_needed > MONTHLY_QUOTA:
        remaining = MONTHLY_QUOTA - monthly_count
        respond(format_error_message("quota_exceeded", kudos_needed=kudos_needed, remaining=remaining))
        return True
    
    # Record kudos for each user
    successful_kudos = []
    failed_kudos = []
    
    for receiver in unique_users:
        if db_manager.record_kudos(user_id, receiver):
            successful_kudos.append(receiver)
        else:
            failed_kudos.append(receiver)
    
    # Send announcements and confirm
    if successful_kudos:
        # Send announcement to channel
        announcement = format_kudos_announcement(user_id, successful_kudos, message)
        logger.info(f"Formatted announcement: {announcement}")
        
        if SLACK_CHANNEL_ID:
            logger.info(f"Posting to channel: {SLACK_CHANNEL_ID}")
            try:
                result = app.client.chat_postMessage(
                    channel=SLACK_CHANNEL_ID,
                    text=announcement,
                    unfurl_links=False
                )
                logger.info(f"Channel post result: {result}")
            except Exception as e:
                logger.error(f"Failed to post to channel: {e}")
        else:
            logger.warning("SLACK_CHANNEL_ID not set, skipping channel announcement")
        
        # Confirm to user
        confirmation = format_kudos_confirmation(monthly_count, kudos_needed, len(successful_kudos), MONTHLY_QUOTA)
        respond(confirmation)
    
    if failed_kudos:
        failed_mentions = " ".join([f"<@{user}>" for user in failed_kudos])
        respond(format_error_message("failed_kudos", failed_mentions=failed_mentions))
    
    return True
