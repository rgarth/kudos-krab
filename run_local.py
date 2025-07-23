#!/usr/bin/env python3
"""
Simple local testing script for Kudos Krab
"""
import os
from dotenv import load_dotenv

def main():
    # Load environment variables from .env file FIRST
    load_dotenv()
    
    # Check required environment variables
    required_vars = [
        'SLACK_BOT_TOKEN',
        'SLACK_SIGNING_SECRET',
        'DATABASE_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease create a .env file with the required variables.")
        print("See env.example for the required format.")
        return
    
    print("🦀 Starting Kudos Krab locally...")
    print("🌊 Bot will be available at: http://localhost:3000")
    print("📝 Make sure your Slack app is configured for local development")
    print("🔧 Use ngrok or similar to expose localhost to Slack")
    print("\nPress Ctrl+C to stop the bot")
    
    # Import and start the bot AFTER environment variables are loaded
    from kudos_bot import app
    app.start(port=3000)

if __name__ == "__main__":
    main() 