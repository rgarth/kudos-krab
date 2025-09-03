import os

# Bot Configuration
MONTHLY_QUOTA = int(os.environ.get("MONTHLY_QUOTA", "10"))
DEFAULT_PERSONALITY = os.environ.get("BOT_PERSONALITY", "crab")

# Server Configuration
DEFAULT_PORT = int(os.environ.get("PORT", "3000"))
