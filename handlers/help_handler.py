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
• `/kk leaderboard Aug` - See August leaderboard (this year or last)
• `/kk leaderboard august 2025` - See August 2025 leaderboard
• `/kk leaderboard 08` - See August leaderboard using month number
• `/kk stats` - Check your own kudos journey
• `/kk help` - Show this help message

*{personality['help']['examples']}*
• `/kk @alice thanks for the awesome help!`
• `/kk @bob @charlie you both crushed that project!`
• `/kk Great work @david on the presentation yesterday`
• `/kk leaderboard july 2025` - Check July 2025 champions

*{personality['help']['tips']}*
• Use full month names: `august`, `july`, `december`
• Use abbreviations: `aug`, `jul`, `dec`
• Use numbers: `08`, `07`, `12`
• If no year specified, shows most recent occurrence

{personality['help']['footer']}"""
    respond(help_text)


def get_app_mention_message():
    """Get the app mention message"""
    from config.personalities import load_personality
    
    personality = load_personality()
    return personality['app_mention']
