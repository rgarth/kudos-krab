def show_help_message(respond, channel_id=None, db_manager=None):
    """Show the help message with all available commands"""
    from config.personalities import load_personality, load_personality_for_channel
    
    if channel_id and db_manager:
        personality = load_personality_for_channel(channel_id, db_manager)
    else:
        personality = load_personality()
    
    help_text = f"""{personality['help']['title']}

*{personality['help']['send_kudos']}*
• `/kk @user message` - Send love to one person
• `/kk @user1 @user2 message` - Spread the love to multiple people
• `/kk Thanks @user for the help!` - Free-form messages work too!

*{personality['help']['commands']}*
• `/kk leaderboard [public]` - See this month's leaders (add 'public' to share)
• `/kk leaderboard Aug|08 [2025] [public]` - See August leaders (year optional)
• `/kk stats` - Check your own kudos journey
• `/kk config` - Show current channel configuration
• `/kk config edit` - Configure channel settings (personality, quota, leaderboard)
• `/kk config default` - Reset channel to default settings
• `/kk help` - Show this help message

{personality['help']['footer']}"""
    respond(help_text)


def get_app_mention_message(channel_id=None, db_manager=None):
    """Get the app mention message"""
    from config.personalities import load_personality, load_personality_for_channel
    
    if channel_id and db_manager:
        personality = load_personality_for_channel(channel_id, db_manager)
    else:
        personality = load_personality()
    return personality['app_mention']
