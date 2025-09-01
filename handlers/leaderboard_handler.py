import logging
from datetime import datetime
from utils.date_parser import parse_month_year, get_target_date
from utils.message_formatter import format_leaderboard, format_error_message

logger = logging.getLogger(__name__)


def handle_leaderboard_command(respond, db_manager, app, params="", channel_id=None, say=None):
    """Handle leaderboard request with optional month/year parameters and public posting"""
    try:
        # Check for public flag
        is_public = False
        if params:
            params_lower = params.lower()
            if "public" in params_lower or "share" in params_lower:
                is_public = True
                # Remove public/share keywords from params for date parsing
                params = params_lower.replace("public", "").replace("share", "").strip()
        
        # Parse month and year from parameters
        month, year = parse_month_year(params)
        target_month, target_year = get_target_date(month, year)
        
        # Log the parsing results for debugging
        logger.info(f"Leaderboard request - params: '{params}', parsed: month={month}, year={year}, target: {target_month}/{target_year}, channel: {channel_id}, public: {is_public}")
        
        # Get leaderboard data for this channel
        leaderboard_data = db_manager.get_monthly_leaderboard(target_month, target_year, channel_id)
        
        # Use the data directly - trust the user IDs in the database
        formatted_leaderboard = format_leaderboard(leaderboard_data, target_month, target_year)
        
        if is_public and say and channel_id:
            # Post to channel publicly
            say(formatted_leaderboard)
            # Also respond to user to confirm
            respond("✅ Leaderboard posted to the channel!")
        else:
            # Respond privately to user
            respond(formatted_leaderboard)
            
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        respond(format_error_message("database_error"))



