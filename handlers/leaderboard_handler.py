import logging
from datetime import datetime
from utils.date_parser import parse_month_year, get_target_date
from utils.message_formatter import format_leaderboard, format_error_message

logger = logging.getLogger(__name__)


def handle_leaderboard_command(respond, db_manager, app, params="", channel_id=None):
    """Handle leaderboard request with optional month/year parameters"""
    try:
        # Parse month and year from parameters
        month, year = parse_month_year(params)
        target_month, target_year = get_target_date(month, year)
        
        # Log the parsing results for debugging
        logger.info(f"Leaderboard request - params: '{params}', parsed: month={month}, year={year}, target: {target_month}/{target_year}, channel: {channel_id}")
        
        # Get leaderboard data for this channel
        leaderboard_data = db_manager.get_monthly_leaderboard(target_month, target_year, channel_id)
        
        # Filter out users who are no longer in Slack
        filtered_data = filter_active_users(leaderboard_data, app)
        
        formatted_leaderboard = format_leaderboard(filtered_data, target_month, target_year)
        respond(formatted_leaderboard)
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        respond(format_error_message("database_error"))


def filter_active_users(leaderboard_data, app):
    """Filter out users who are no longer in Slack"""
    try:
        # Get all active users from Slack
        users_response = app.client.users_list()
        active_user_ids = {user['id'] for user in users_response['members'] if not user.get('deleted', False)}
        
        # Filter senders
        filtered_senders = []
        for sender, count in leaderboard_data['senders']:
            if sender in active_user_ids:
                filtered_senders.append((sender, count))
        
        # Filter receivers
        filtered_receivers = []
        for receiver, count in leaderboard_data['receivers']:
            if receiver in active_user_ids:
                filtered_receivers.append((receiver, count))
        
        logger.info(f"Filtered leaderboard - senders: {len(filtered_senders)}/{len(leaderboard_data['senders'])}, receivers: {len(filtered_receivers)}/{len(leaderboard_data['receivers'])}")
        
        return {
            'senders': filtered_senders,
            'receivers': filtered_receivers
        }
    except Exception as e:
        logger.error(f"Error filtering active users: {e}")
        # If filtering fails, return original data
        return leaderboard_data
