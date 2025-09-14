import logging
from datetime import datetime
from config.settings import MONTHLY_QUOTA
from utils.user_utils import (
    extract_user_mentions, 
    extract_message_text, 
    remove_duplicate_users,
    validate_kudos_recipients,
    get_bot_user_id
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
    channel_id = command.get("channel_id")
    
    # Debug: Log the full command object to see what Slack sends
    logger.info(f"Full command object: {command}")
    
    # Parse kudos command: anything else is treated as a kudos message
    if not text:
        respond(format_error_message("no_mentions", channel_id, db_manager))
        return True
    
    # Extract all mentioned users (these are already user IDs)
    mentioned_users = extract_user_mentions(text)
    
    # Debug: Log what we received
    logger.info(f"Received text: '{text}'")
    logger.info(f"Extracted user IDs: {mentioned_users}")
    
    if not mentioned_users:
        respond(format_error_message("no_mentions", channel_id, db_manager))
        return True
    
    # Remove duplicates while preserving order
    unique_users = remove_duplicate_users(mentioned_users)
    
    # Validate recipients
    bot_user_id = get_bot_user_id(app)
    logger.info(f"Validating recipients - user_id: {user_id}, unique_users: {unique_users}, bot_user_id: {bot_user_id}")
    validation_errors = validate_kudos_recipients(user_id, unique_users, bot_user_id)
    logger.info(f"Validation errors: {validation_errors}")
    
    if "self_kudos" in validation_errors:
        respond(format_error_message("self_kudos", channel_id, db_manager))
        return True
    
    if "bot_kudos" in validation_errors:
        respond(format_error_message("bot_kudos", channel_id, db_manager))
        return True
    
    # Extract message
    message = extract_message_text(text)
    if not message:
        respond(format_error_message("empty_message", channel_id, db_manager))
        return True
    
    # Check monthly quota for multiple kudos
    current_month = datetime.now().month
    current_year = datetime.now().year
    monthly_count = db_manager.get_monthly_kudos_count(user_id, current_month, current_year, channel_id)
    kudos_needed = len(unique_users)
    
    # Get channel-specific quota (with inheritance from override channel)
    config = db_manager.get_channel_config(channel_id)
    if config and config['leaderboard_channel_id']:
        # Channel override active - get quota from target channel
        target_config = db_manager.get_channel_config(config['leaderboard_channel_id'])
        monthly_quota = target_config['monthly_quota'] if target_config and target_config['monthly_quota'] else MONTHLY_QUOTA
    else:
        # Normal channel - use own quota
        monthly_quota = config['monthly_quota'] if config and config['monthly_quota'] else MONTHLY_QUOTA
    
    if monthly_count + kudos_needed > monthly_quota:
        remaining = monthly_quota - monthly_count
        respond(format_error_message("quota_exceeded", channel_id, db_manager, kudos_needed=kudos_needed, remaining=remaining))
        return True
    
    # Record kudos for each user
    successful_kudos = []
    failed_kudos = []
    
    for receiver in unique_users:
        if db_manager.record_kudos(user_id, receiver, channel_id):
            successful_kudos.append(receiver)
        else:
            failed_kudos.append(receiver)
    
    # Send announcements and confirm
    if successful_kudos:
        # Send announcement to the same channel where the command was issued
        announcement = format_kudos_announcement(user_id, successful_kudos, message, channel_id, db_manager)
        logger.info(f"Formatted announcement: {announcement}")
        
        logger.info(f"Posting to channel: {channel_id}")
        try:
            result = app.client.chat_postMessage(
                channel=channel_id,
                text=announcement,
                unfurl_links=False
            )
            logger.info(f"Channel post result: {result}")
        except Exception as e:
            logger.error(f"Failed to post to channel: {e}")
        
        # Confirm to user
        confirmation = format_kudos_confirmation(monthly_count, kudos_needed, len(successful_kudos), monthly_quota, channel_id, db_manager)
        respond(confirmation)
    
    if failed_kudos:
        failed_mentions = " ".join([f"<@{user}>" for user in failed_kudos])
        respond(format_error_message("failed_kudos", channel_id, db_manager, failed_mentions=failed_mentions))
    
    return True
