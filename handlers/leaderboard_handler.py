import logging
from datetime import datetime
from utils.date_parser import parse_month_year, get_target_date
from utils.message_formatter import format_leaderboard, format_error_message
from config.personalities import load_personality

logger = logging.getLogger(__name__)


def handle_leaderboard_command(respond, db_manager, app, params="", channel_id=None, say=None):
    """Handle leaderboard request with optional month/year parameters and public posting"""
    try:
        # Check for public flag and complete flag
        is_public = False
        is_complete = False
        if params:
            params_lower = params.lower()
            if "public" in params_lower or "share" in params_lower:
                is_public = True
                # Remove public/share keywords from params for date parsing
                params = params_lower.replace("public", "").replace("share", "").strip()
            if "complete" in params_lower:
                is_complete = True
                # Remove complete keyword from params for date parsing
                params = params_lower.replace("complete", "").strip()
        
        # Parse month and year from parameters
        month, year = parse_month_year(params)
        
        # If no specific month/year provided, use current month/year in channel's timezone
        if month is None and year is None:
            target_month, target_year = db_manager.get_current_month_year_in_timezone(channel_id)
        else:
            target_month, target_year = get_target_date(month, year)
        
        # Complete leaderboard only works for current month
        if is_complete and (month is not None or year is not None):
            respond("❌ Complete leaderboard is only available for the current month.")
            return
        
        # Log the parsing results for debugging
        logger.info(f"Leaderboard request - params: '{params}', parsed: month={month}, year={year}, target: {target_month}/{target_year}, channel: {channel_id}, public: {is_public}, complete: {is_complete}")
        
        # Get effective leaderboard channel (handles channel overrides)
        effective_channel_id = db_manager.get_effective_leaderboard_channel(channel_id)
        
        # Get leaderboard data for the effective channel
        if is_complete:
            # Get complete leaderboard (all users, no limit) - current month only
            leaderboard_data = db_manager.get_complete_monthly_leaderboard(target_month, target_year, effective_channel_id)
        else:
            # Get regular leaderboard with channel-specific limit
            leaderboard_data = db_manager.get_monthly_leaderboard(target_month, target_year, effective_channel_id)
        
        # Use the data directly - trust the user IDs in the database
        formatted_leaderboard = format_leaderboard(leaderboard_data, target_month, target_year, channel_id, db_manager)
        
        if is_public and say and channel_id:
            # Post to channel publicly
            say(formatted_leaderboard)
            # Also respond to user to confirm
            personality = load_personality()
            respond(personality['leaderboard']['posted_confirmation'])
        else:
            # Respond privately to user
            respond(formatted_leaderboard)
            
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        respond(format_error_message("database_error", channel_id, db_manager))



