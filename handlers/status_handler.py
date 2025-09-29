"""
Status handler for the Kudos Krab bot.
Shows bot health, installed channels, and operational statistics.
"""

import logging
from datetime import datetime
from config.personalities import load_personality_for_channel

logger = logging.getLogger(__name__)

def handle_status_command(ack, respond, channel_id, db_manager, client):
    """Handle the /kk status command to show bot operational status."""
    ack()
    
    try:
        # Load personality for this channel
        personality = load_personality_for_channel(channel_id, db_manager)
        
        # Get bot status information
        status_info = get_bot_status(db_manager, client)
        
        # Format the status message
        message = format_status_message(status_info, personality, db_manager)
        
        # Send response (ephemeral - only visible to the user)
        respond(message, response_type="ephemeral")
        
    except Exception as e:
        logger.error(f"Failed to get bot status: {e}")
        respond("❌ Failed to get bot status. Check logs for details.", response_type="ephemeral")

def get_bot_status(db_manager, client):
    """Get comprehensive bot status information."""
    try:
        # Get bot authentication info (with error handling to prevent hanging)
        bot_info = {'bot_id': 'Unknown', 'user_id': 'Unknown', 'team': 'Unknown', 'team_id': 'Unknown', 'url': 'Unknown'}
        try:
            auth_response = client.auth_test()
            bot_info = {
                'bot_id': auth_response.get('bot_id', 'Unknown'),
                'user_id': auth_response.get('user_id', 'Unknown'),
                'team': auth_response.get('team', 'Unknown'),
                'team_id': auth_response.get('team_id', 'Unknown'),
                'url': auth_response.get('url', 'Unknown')
            }
        except Exception as e:
            logger.warning(f"Failed to get bot auth info: {e}")
        
        # Use single database connection for all queries
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Get all channels with kudos activity OR custom configs
                channels_query = """
                SELECT DISTINCT channel_id 
                FROM kudos 
                UNION
                SELECT DISTINCT channel_id 
                FROM channel_configs
                ORDER BY channel_id
                """
                cursor.execute(channels_query)
                channels = [row[0] for row in cursor.fetchall()]
                
                # Get last kudos timestamp
                last_kudos_query = """
                SELECT timestamp, channel_id, sender, receiver
                FROM kudos 
                ORDER BY timestamp DESC 
                LIMIT 1
                """
                cursor.execute(last_kudos_query)
                last_kudos_row = cursor.fetchone()
                
                # Get total kudos count
                total_kudos_query = "SELECT COUNT(*) FROM kudos"
                cursor.execute(total_kudos_query)
                total_kudos = cursor.fetchone()[0]
                
                # Get channels with custom configs
                config_channels_query = """
                SELECT channel_id, personality_name, monthly_quota, leaderboard_channel_id
                FROM channel_configs
                ORDER BY channel_id
                """
                cursor.execute(config_channels_query)
                config_channels = cursor.fetchall()
        
        return {
            'bot_info': bot_info,
            'channels': channels,
            'last_kudos': last_kudos_row,
            'total_kudos': total_kudos,
            'config_channels': config_channels,
            'timestamp': datetime.now()
        }
        
    except Exception as e:
        logger.error(f"Failed to get bot status from database: {e}")
        raise

def format_status_message(status_info, personality, db_manager):
    """Format the status information into a readable message."""
    bot_info = status_info['bot_info']
    channels = status_info['channels']
    last_kudos = status_info['last_kudos']
    total_kudos = status_info['total_kudos']
    config_channels = status_info['config_channels']
    timestamp = status_info['timestamp']
    
    # Bot status
    message = f"🤖 *Kudos Krab Bot Status*\n"
    message += f"🟢 *Status:* Online\n"
    message += f"⏰ *Checked:* {timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
    message += f"🏢 *Workspace:* {bot_info.get('team', 'Unknown')}\n"
    message += f"🔗 *URL:* {bot_info.get('url', 'Unknown')}\n"
    message += f"🆔 *Bot ID:* {bot_info.get('bot_id', 'Unknown')}\n\n"
    
    # Channels (combined from kudos activity and custom configs)
    if channels:
        channel_list = ", ".join([f"<#{ch}>" for ch in channels])
        message += f"📺 *Active Channels:* {channel_list}\n"
    else:
        message += f"📺 *Active Channels:* None\n"
    
    # Last kudos
    if last_kudos:
        last_time, last_channel, sender, receiver = last_kudos
        time_ago = timestamp - last_time
        hours_ago = int(time_ago.total_seconds() / 3600)
        minutes_ago = int((time_ago.total_seconds() % 3600) / 60)
        
        if hours_ago > 0:
            time_str = f"{hours_ago}h {minutes_ago}m ago"
        else:
            time_str = f"{minutes_ago}m ago"
            
        message += f"🎉 *Last Kudos:* {time_str} in <#{last_channel}>\n"
    else:
        message += f"🎉 *Last Kudos:* Never\n"
    
    # Total kudos
    message += f"📊 *Total Kudos:* {total_kudos:,}\n\n"
    
    # Custom configurations
    if config_channels:
        message += f"⚙️ *Custom Configurations:*\n"
        for channel_id, personality_name, quota, leaderboard in config_channels:
            # Get effective values (inherited from override channel if applicable)
            effective_channel = db_manager.get_effective_leaderboard_channel(channel_id)
            effective_config = db_manager.get_channel_config(effective_channel)
            
            # Build config line
            if effective_channel != channel_id:
                # Channel inherits from another channel
                config_line = f"• <#{channel_id}>: config from <#{effective_channel}>"
            else:
                # Own configuration - show the actual values
                if effective_config and effective_config['personality_name']:
                    effective_personality = effective_config['personality_name']
                else:
                    effective_personality = "default"
                
                if effective_config and effective_config['monthly_quota']:
                    effective_quota = effective_config['monthly_quota']
                else:
                    effective_quota = "default"
                
                config_line = f"• <#{channel_id}>: {effective_personality}, quota: {effective_quota}"
            
            if leaderboard:
                config_line += f", leaderboard: <#{leaderboard}>"
            message += f"{config_line}\n"
    else:
        message += f"⚙️ *Custom Configurations:* None (all using defaults)\n"
    
    return message
