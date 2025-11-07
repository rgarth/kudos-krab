import logging
import re
from datetime import datetime
from utils.date_parser import parse_month_year, get_target_date
from utils.message_formatter import format_leaderboard, format_error_message
from utils.user_utils import get_channel_id_from_name
from config.personalities import load_personality

logger = logging.getLogger(__name__)


def parse_leaderboard_params(params):
    """
    Parse flexible leaderboard command parameters.
    Extracts: channel name/ID, flags (public, complete), and date information.
    Handles parameters in any order.
    
    Returns: (target_channel_id_or_name, is_public, is_complete, date_params)
    """
    if not params:
        return None, False, False, ""
    
    params_lower = params.lower()
    
    # First, check for Slack's channel mention format: <#C123456|channel-name> or <#C123456>
    # This is what Slack sends when "Escape channels, users, and links" is enabled
    channel_id_or_name = None
    slack_channel_match = re.search(r'<#([C][A-Z0-9]+)(?:\|[^>]*)?>', params)
    if slack_channel_match:
        # Slack already converted it to a channel ID!
        channel_id_or_name = slack_channel_match.group(1)  # Just the ID part
        logger.info(f"Found Slack channel mention format: {channel_id_or_name}")
    else:
        # Fall back to looking for #channelname format (raw text)
        channel_match = re.search(r'#([a-z0-9_-]+)', params, re.IGNORECASE)
        if channel_match:
            channel_id_or_name = channel_match.group(0)  # Keep the # in the name
    
    # Extract flags
    is_public = "public" in params_lower or "share" in params_lower
    is_complete = "complete" in params_lower
    
    # Extract date params - everything except channel name/ID and flags
    date_params = params
    if channel_id_or_name:
        # Remove both Slack format <#C123|name> and raw #name format
        date_params = re.sub(r'<#[^>]+>', '', date_params)  # Remove <#C123|name>
        date_params = re.sub(r'#' + re.escape(channel_id_or_name.lstrip('#')), '', date_params, flags=re.IGNORECASE)  # Remove #name
        date_params = date_params.strip()
    if is_public:
        # Remove public/share keywords
        date_params = re.sub(r'\b(public|share)\b', '', date_params, flags=re.IGNORECASE).strip()
    if is_complete:
        date_params = re.sub(r'\bcomplete\b', '', date_params, flags=re.IGNORECASE).strip()
    
    # Clean up extra spaces
    date_params = re.sub(r'\s+', ' ', date_params).strip()
    
    return channel_id_or_name, is_public, is_complete, date_params


def handle_leaderboard_command(respond, db_manager, app, params="", channel_id=None, say=None):
    """Handle leaderboard request with optional month/year parameters, channel name, and public posting"""
    try:
        # Debug: Log what we received from Slack
        logger.info(f"Leaderboard command received - raw params: '{params}'")
        
        # Parse flexible parameters
        target_channel_id_or_name, is_public, is_complete, date_params = parse_leaderboard_params(params)
        logger.info(f"Parsed - channel: {target_channel_id_or_name}, public: {is_public}, complete: {is_complete}, date: '{date_params}'")
        
        # If a channel was specified, determine the channel ID
        target_channel_id = channel_id  # Default to current channel
        if target_channel_id_or_name:
            # Check if it's already a channel ID (from Slack's <#C123> format or starts with C/G/D)
            if target_channel_id_or_name.startswith('C') or target_channel_id_or_name.startswith('G') or target_channel_id_or_name.startswith('D'):
                # Already a channel ID (from Slack's escaped format or user typed ID directly)
                target_channel_id = target_channel_id_or_name
                logger.info(f"Using channel ID directly from Slack escaped format: {target_channel_id}")
            else:
                # It's a channel name (raw text), need to look it up
                # Note: This should rarely happen if "Escape channels" is enabled in Slack app settings
                logger.warning(f"Received raw channel name '{target_channel_id_or_name}' - Slack should escape this if 'Escape channels' is enabled")
                try:
                    looked_up_id = get_channel_id_from_name(app.client, target_channel_id_or_name)
                    if looked_up_id:
                        target_channel_id = looked_up_id
                        logger.info(f"Looked up channel name {target_channel_id_or_name} -> {target_channel_id}")
                    else:
                        respond(f"❌ Channel {target_channel_id_or_name} not found. Only public channels can be accessed by name. If this is a private channel, use the leaderboard command from within that channel.")
                        return
                except Exception as e:
                    error_msg = str(e)
                    if "missing required scope" in error_msg.lower() or "missing required scopes" in error_msg.lower():
                        respond(f"❌ {error_msg}\n\nTo use channel names in leaderboard commands, either:\n1. Enable 'Escape channels, users, and links' in your Slack app slash command settings (recommended - no scope needed), or\n2. Add the `channels:read` scope to your Slack app (OAuth & Permissions > Scopes > Bot Token Scopes).")
                    else:
                        respond(f"❌ Error looking up channel {target_channel_id_or_name}: {error_msg}")
                    return
        
        # Parse month and year from date parameters
        month, year = parse_month_year(date_params)
        
        # If no specific month/year provided, use current month/year in channel's timezone
        if month is None and year is None:
            target_month, target_year = db_manager.get_current_month_year_in_timezone(target_channel_id)
        else:
            target_month, target_year = get_target_date(month, year)
        
        # Complete leaderboard only works for current month
        if is_complete and (month is not None or year is not None):
            respond("❌ Complete leaderboard is only available for the current month.")
            return
        
        # Log the parsing results for debugging
        logger.info(f"Leaderboard request - params: '{params}', parsed: month={month}, year={year}, target: {target_month}/{target_year}, channel: {target_channel_id}, public: {is_public}, complete: {is_complete}")
        
        # Get effective leaderboard channel (handles channel overrides)
        effective_channel_id = db_manager.get_effective_leaderboard_channel(target_channel_id)
        
        # Get leaderboard data for the effective channel
        if is_complete:
            # Get complete leaderboard (all users, no limit) - current month only
            leaderboard_data = db_manager.get_complete_monthly_leaderboard(target_month, target_year, effective_channel_id)
        else:
            # Get regular leaderboard with channel-specific limit
            leaderboard_data = db_manager.get_monthly_leaderboard(target_month, target_year, effective_channel_id)
        
        # Use the data directly - trust the user IDs in the database
        formatted_leaderboard = format_leaderboard(leaderboard_data, target_month, target_year, target_channel_id, db_manager)
        
        # For public posting, always post to the channel where the command was issued
        # target_channel_id is only for determining which leaderboard data to show
        if is_public and app.client and channel_id:
            # Post to the channel where the command was issued (could be a DM or channel)
            try:
                app.client.chat_postMessage(
                    channel=channel_id,
                    text=formatted_leaderboard
                )
                # Also respond to user to confirm
                personality = load_personality()
                respond(personality['leaderboard']['posted_confirmation'])
            except Exception as e:
                logger.error(f"Error posting leaderboard to channel: {e}")
                respond(f"❌ Failed to post leaderboard to channel. {str(e)}")
        else:
            # Respond privately to user
            respond(formatted_leaderboard)
            
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        respond(format_error_message("database_error", channel_id, db_manager))



