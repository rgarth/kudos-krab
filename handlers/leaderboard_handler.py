import logging
from datetime import datetime
from utils.date_parser import parse_month_year, get_target_date
from utils.message_formatter import format_leaderboard, format_error_message

logger = logging.getLogger(__name__)


def handle_leaderboard_command(respond, db_manager, params=""):
    """Handle leaderboard request with optional month/year parameters"""
    try:
        # Parse month and year from parameters
        month, year = parse_month_year(params)
        target_month, target_year = get_target_date(month, year)
        
        # Log the parsing results for debugging
        logger.info(f"Leaderboard request - params: '{params}', parsed: month={month}, year={year}, target: {target_month}/{target_year}")
        
        # Get leaderboard data
        leaderboard_data = db_manager.get_monthly_leaderboard(target_month, target_year)
        formatted_leaderboard = format_leaderboard(leaderboard_data, target_month, target_year)
        respond(formatted_leaderboard)
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        respond(format_error_message("database_error"))
