from datetime import datetime
from config.personalities import load_personality


def format_leaderboard(leaderboard_data, month, year):
    """Format leaderboard data for Slack message"""
    personality = load_personality()
    month_name = datetime(year, month, 1).strftime("%B %Y")
    
    # Format top senders
    senders_text = f"*{personality['leaderboard']['senders_title']}*\n"
    if leaderboard_data['senders']:
        for i, (sender, count) in enumerate(leaderboard_data['senders'], 1):
            senders_text += f"{i}. <@{sender}> - {count} kudos 🌊\n"
    else:
        senders_text += f"{personality['leaderboard']['no_senders']}\n"
    
    # Format top receivers
    receivers_text = f"\n*{personality['leaderboard']['receivers_title']}*\n"
    if leaderboard_data['receivers']:
        for i, (receiver, count) in enumerate(leaderboard_data['receivers'], 1):
            receivers_text += f"{i}. <@{receiver}> - {count} kudos 🐚\n"
    else:
        receivers_text += f"{personality['leaderboard']['no_receivers']}\n"
    
    title = personality['leaderboard']['title'].format(month_name=month_name)
    footer = personality['leaderboard']['footer']
    
    return f"*{title}*\n\n{senders_text}{receivers_text}\n\n*{footer}*"


def format_kudos_announcement(user_id, successful_kudos, message):
    """Format kudos announcement message"""
    personality = load_personality()
    
    if len(successful_kudos) == 1:
        template = personality['success']['announcement_single']
        return template.format(user_id=user_id, receiver=successful_kudos[0], message=message)
    else:
        user_mentions = " ".join([f"<@{user}>" for user in successful_kudos])
        template = personality['success']['announcement_multiple']
        return template.format(user_id=user_id, receivers=user_mentions, message=message)


def format_kudos_confirmation(monthly_count, kudos_needed, successful_count, monthly_quota):
    """Format kudos confirmation message"""
    personality = load_personality()
    remaining = monthly_quota - monthly_count - successful_count
    
    if successful_count == 1:
        template = personality['success']['kudos_single']
        return template.format(remaining=remaining)
    else:
        template = personality['success']['kudos_multiple']
        return template.format(count=successful_count, remaining=remaining)


def format_stats_message(user_id, monthly_sent, monthly_received, monthly_quota, total_sent, total_received):
    """Format user stats message"""
    personality = load_personality()
    
    return f"""{personality['stats']['title']}

*{personality['stats']['this_month']}*
• {personality['stats']['kudos_sent']} {monthly_sent} 🌊
• {personality['stats']['kudos_received']} {monthly_received} 🐚
• {personality['stats']['remaining']} {monthly_quota - monthly_sent} ✨

*{personality['stats']['all_time']}*
• {personality['stats']['total_sent']} {total_sent} 🚀
• {personality['stats']['total_received']} {total_received} 💎

*{personality['stats']['footer']}*"""


def format_error_message(error_type, **kwargs):
    """Format error messages"""
    personality = load_personality()
    error_messages = personality['errors']
    
    if error_type in error_messages:
        template = error_messages[error_type]
        return template.format(**kwargs)
    
    return "Something went wrong, buddy! 🦀"
