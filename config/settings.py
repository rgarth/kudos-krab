import os

# Bot Configuration
MONTHLY_QUOTA = int(os.environ.get("MONTHLY_QUOTA", "10"))
SLACK_BOT_USER_ID = os.environ.get("SLACK_BOT_USER_ID")

# Server Configuration
DEFAULT_PORT = int(os.environ.get("PORT", "3000"))
