import os
import json
from pathlib import Path

# Default personality
DEFAULT_PERSONALITY = "crab"

def load_personality(personality_name=None):
    """Load personality responses from JSON file"""
    if personality_name is None:
        personality_name = os.environ.get("BOT_PERSONALITY", DEFAULT_PERSONALITY)
    
    # Path to personality files
    personality_dir = Path(__file__).parent.parent / "personalities"
    personality_file = personality_dir / f"{personality_name}.json"
    
    # Load default personality if requested one doesn't exist
    if not personality_file.exists():
        default_file = personality_dir / f"{DEFAULT_PERSONALITY}.json"
        if default_file.exists():
            personality_file = default_file
        else:
            # Return hardcoded defaults if no files exist
            return get_default_responses()
    
    try:
        with open(personality_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading personality {personality_name}: {e}")
        return get_default_responses()


def get_default_responses():
    """Fallback responses if personality file can't be loaded"""
    return {
        "help": {
            "title": "HEY THERE, BUDDY! 🦀 Here's how to make some waves:",
            "send_kudos": "🎯 Send Kudos:",
            "commands": "📊 Commands:",
            "examples": "💡 Examples:",
            "tips": "🌊 Leaderboard Tips:",
            "footer": "Now go make some magic, bud! 🌊✨"
        },
        "errors": {
            "no_mentions": "HEY THERE, BUD! 🦀 You gotta mention someone with @username to send them some love! 🌊 Don't be shy, dude - spread those good vibes! ✨\n\nTry `/kk help` to see how to use the bot!",
            "user_not_found": "OOPS, BUDDY! 😅 I couldn't find a user with username @{username}! 🦀 Make sure you're using the correct username, friend! 🌊",
            "self_kudos": "NICE TRY, BUDDY! 😂 But you can't give yourself kudos, you silly crab! 🦀 Save that self-love for someone else, friend! 🌊✨ Maybe try giving yourself a high-five instead? 🤚",
            "bot_kudos": "AWWW, BUDDY! 🥺 You're trying to give ME kudos? That's so sweet! 🦀 *blushes in crab* 🌊✨ But I'm just here to help spread the love - save those kudos for your amazing teammates! 💕 Maybe try `/kk help` to see how to send kudos to others? 🦀",
            "empty_message": "COME ON, BUD! 🦀 You can't just send empty kudos! 🌊 Add some words to make it special, friend - that's what makes the ocean sparkle! ✨",
            "quota_exceeded": "YIKES, BUDDY! 😅 Looks like you're all out of kudos juice! 🦀 You need {kudos_needed} more but only have {remaining} left this month, friend. Time to wait for the next tide to roll in! 🌊",
            "failed_kudos": "OOPS, BUDDY! 😅 Looks like the ocean got a bit choppy for {failed_mentions}! 🦀 Let's try that again, friend - the tide will be better this time! 🌊",
            "database_error": "YIKES, BUDDY! 😅 The ocean got a bit rough while I was checking the leaderboard! 🦀 Let's try that again, friend - the waves should be calmer now! 🌊",
            "stats_error": "OOPS, BUDDY! 😅 The ocean got a bit murky while I was checking your stats! 🦀 Let's try that again, friend - the water should be clearer now! 🌊"
        },
        "success": {
            "kudos_single": "BOOM, BUDDY! 💥 Kudos delivered like a tidal wave! 🦀 You've got {remaining} more kudos left this month, friend - keep that energy flowing! 🌊✨",
            "kudos_multiple": "WHOA, BUD! 🚀 You just made it RAIN kudos on {count} people! 🦀 That's {remaining} more kudos in your tank, friend - you're on FIRE! 🔥🌊",
            "announcement_single": "🦀 *OH SNAP!* 🦀\n<@{user_id}> just dropped some MAJOR kudos on <@{receiver}>! 🌊\n\n> {message}\n\n*That's what I'm talking about!* 🦀✨",
            "announcement_multiple": "🦀 *HOLY CRAB!* 🦀\n<@{user_id}> just went FULL OCEAN MODE and sent kudos to {receivers}! 🌊🐚\n\n> {message}\n\n*Now THAT'S how you make waves!* 🦀✨"
        },
        "app_mention": "HEY THERE, BUDDY! 🦀 I'm your favorite kudos coach! 🌊\n\nHere's how to make some waves:\n• `/kk @user message` - Send love to one person\n• `/kk @user1 @user2 message` - Spread the love to multiple people\n• `/kk leaderboard` - See who's making the biggest splash\n• `/kk leaderboard Aug 2025` - See specific month/year\n• `/kk stats` - Check your own kudos journey\n\nLet's make this ocean sparkle, bud! ✨"
    }
