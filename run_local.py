#!/usr/bin/env python3
"""
Local development server for Kudos Krab
"""
import os
from dotenv import load_dotenv

# Load environment variables BEFORE importing kudos_bot
load_dotenv()

from kudos_bot import app

# Add health check endpoint for Docker
@app.route("/health")
def health_check():
    return {"status": "healthy", "service": "kudos-krab"}, 200

if __name__ == "__main__":
    print("🦀 Starting Kudos Krab locally on port 3000...")
    print("🌊 Make sure your Slack app Request URL is set to: https://your-ngrok-url.ngrok.io/slack/events")
    app.start(port=3000, path="/slack/events") 