#!/usr/bin/env python3
"""
Local development server for Kudos Krab
"""
import os
from dotenv import load_dotenv

# Load environment variables BEFORE importing kudos_bot
load_dotenv()

from kudos_bot import app

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "3000"))
    print(f"🦀 Starting Kudos Krab locally on port {port}...")
    print(f"🌊 Your Slack app Request URL should be: https://your-domain.com/slack/events")
    app.start(port=port, path="/slack/events", access_log=False) 