# Bot Personalities

This directory contains personality files that define the bot's tone, responses, and messaging style.

## How it works

- Each personality is defined in a JSON file (e.g., `crab.json`)
- The bot loads the personality specified in the `BOT_PERSONALITY` environment variable
- If no personality is specified, it defaults to `crab`
- If the specified personality file doesn't exist, it falls back to the default

## Creating a new personality

1. Create a new JSON file in this directory (e.g., `professional.json`)
2. Follow the structure of `crab.json`
3. Set `BOT_PERSONALITY=professional` in your environment variables

## Personality structure

Each personality JSON file should contain:

```json
{
  "name": "Personality Name",
  "description": "Description of the personality",
  "help": {
    "title": "Help title",
    "send_kudos": "Send kudos section title",
    "commands": "Commands section title",
    "examples": "Examples section title",
    "tips": "Tips section title",
    "footer": "Help footer"
  },
  "errors": {
    "no_mentions": "Error message for no mentions",
    "user_not_found": "Error message for user not found",
    "self_kudos": "Error message for self kudos",
    "bot_kudos": "Error message for bot kudos",
    "empty_message": "Error message for empty message",
    "quota_exceeded": "Error message for quota exceeded",
    "failed_kudos": "Error message for failed kudos",
    "database_error": "Error message for database errors",
    "stats_error": "Error message for stats errors"
  },
  "success": {
    "kudos_single": "Success message for single kudos",
    "kudos_multiple": "Success message for multiple kudos",
    "announcement_single": "Announcement for single kudos",
    "announcement_multiple": "Announcement for multiple kudos"
  },
  "app_mention": "Message when bot is mentioned",
  "leaderboard": {
    "title": "Leaderboard title with {month_name} placeholder",
    "senders_title": "Senders section title",
    "receivers_title": "Receivers section title",
    "no_senders": "Message when no senders",
    "no_receivers": "Message when no receivers",
    "footer": "Leaderboard footer"
  },
  "stats": {
    "title": "Stats title",
    "this_month": "This month section title",
    "all_time": "All time section title",
    "kudos_sent": "Kudos sent label",
    "kudos_received": "Kudos received label",
    "remaining": "Remaining label",
    "total_sent": "Total sent label",
    "total_received": "Total received label",
    "footer": "Stats footer"
  }
}
```

## Template variables

Some messages support template variables:

- `{username}` - Username in error messages
- `{kudos_needed}` - Number of kudos needed
- `{remaining}` - Remaining kudos
- `{failed_mentions}` - Failed user mentions
- `{user_id}` - User ID in announcements
- `{receiver}` - Single receiver in announcements
- `{receivers}` - Multiple receivers in announcements
- `{message}` - Kudos message
- `{count}` - Number of people
- `{month_name}` - Month name in leaderboard title

## Current personalities

- **crab** - Overly enthusiastic with crab/ocean puns and summer camp counselor energy (default)
- **spooky** - Spooky Halloween personality with ghostly puns and eerie enthusiasm
- **buddy** - Buddy the Elf personality with corny Christmas sayings and holiday cheer
