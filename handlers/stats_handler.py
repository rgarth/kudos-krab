import logging
from datetime import datetime
from config.settings import MONTHLY_QUOTA
from utils.message_formatter import format_stats_message, format_error_message

logger = logging.getLogger(__name__)


def handle_stats_command(user_id, respond, db_manager, channel_id=None):
    """Handle stats request"""
    try:
        current_month = datetime.now().month
        current_year = datetime.now().year
        monthly_sent = db_manager.get_monthly_kudos_count(user_id, current_month, current_year, channel_id)
        monthly_received = db_manager.get_monthly_kudos_received_count(user_id, current_month, current_year, channel_id)
        
        user_stats = db_manager.get_user_stats(user_id, channel_id)
        
        stats_message = format_stats_message(
            user_id=user_id,
            monthly_sent=monthly_sent,
            monthly_received=monthly_received,
            monthly_quota=MONTHLY_QUOTA,
            total_sent=user_stats['total_sent'],
            total_received=user_stats['total_received']
        )
        
        respond(stats_message)
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        respond(format_error_message("stats_error"))
