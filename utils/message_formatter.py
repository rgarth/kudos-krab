from datetime import datetime
from config.personalities import load_personality
import random


def format_leaderboard(leaderboard_data, month, year):
    """Format leaderboard data for Slack message"""
    personality = load_personality()
    month_name = datetime(year, month, 1).strftime("%B %Y")
    
    # Format top receivers (most important - show first)
    receivers_text = f"*{personality['leaderboard']['receivers_title']}*\n"
    if leaderboard_data['receivers']:
        for i, (receiver, count) in enumerate(leaderboard_data['receivers'], 1):
            receivers_text += f"{i}. <@{receiver}> - {count} kudos 🐚\n"
    else:
        receivers_text += f"{personality['leaderboard']['no_receivers']}\n"
    
    # Format top senders (simplified - only show top sender(s))
    senders_text = f"\n*{personality['leaderboard']['senders_title']}*\n"
    if leaderboard_data['senders']:
        top_count = leaderboard_data['senders'][0][1]  # Get the highest count
        top_senders = [sender for sender, count in leaderboard_data['senders'] if count == top_count]
        
        if len(top_senders) == 1:
            senders_text += personality['leaderboard']['top_sender_single'].format(
                sender=top_senders[0], count=top_count
            ) + "\n"
        else:
            # Multiple senders tied for first place
            sender_mentions = ", ".join([f"<@{sender}>" for sender in top_senders])
            senders_text += personality['leaderboard']['top_sender_multiple'].format(
                senders=sender_mentions, count=top_count
            ) + "\n"
    else:
        senders_text += f"{personality['leaderboard']['no_senders']}\n"
    
    title = personality['leaderboard']['title'].format(month_name=month_name)
    footer = personality['leaderboard']['footer']
    
    return f"*{title}*\n\n{receivers_text}{senders_text}\n\n*{footer}*"


def format_kudos_announcement(user_id, successful_kudos, message):
    """Format kudos announcement message"""
    personality = load_personality()
    
    if len(successful_kudos) == 1:
        template = personality['success']['announcement_single']
        # Handle both single strings and arrays
        if isinstance(template, list):
            template = random.choice(template)
        return template.format(user_id=user_id, receiver=successful_kudos[0], message=message)
    else:
        user_mentions = " ".join([f"<@{user}>" for user in successful_kudos])
        template = personality['success']['announcement_multiple']
        # Handle both single strings and arrays
        if isinstance(template, list):
            template = random.choice(template)
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
        # Handle both single strings and arrays
        if isinstance(template, list):
            template = random.choice(template)
        return template.format(**kwargs)
    
    return "Something went wrong, buddy! 🦀"
