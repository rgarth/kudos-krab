def show_help_message(respond):
    """Show the help message with all available commands"""
    from config.personalities import load_personality
    
    personality = load_personality()
    
    help_text = f"""{personality['help']['title']}

*{personality['help']['send_kudos']}*
• `/kk @user message` - Send love to one person
• `/kk @user1 @user2 message` - Spread the love to multiple people
• `/kk Thanks @user for the help!` - Free-form messages work too!

*{personality['help']['commands']}*
• `/kk leaderboard` - See who's making the biggest splash this month
• `/kk leaderboard Aug|08 [2025]` - See August leaderboard (year is optional)
• `/kk stats` - Check your own kudos journey
• `/kk help` - Show this help message

{personality['help']['footer']}"""
    respond(help_text)


def get_app_mention_message():
    """Get the app mention message"""
    from config.personalities import load_personality
    
    personality = load_personality()
    return personality['app_mention']
