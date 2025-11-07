# Slack App Setup Guide for Kiitos Krab 🦀

This guide will walk you through creating and configuring a Slack app for Kiitos Krab from scratch.

## Step 1: Create a New Slack App

1. Go to [https://api.slack.com/apps](https://api.slack.com/apps)
2. Click **"Create New App"**
3. Choose **"From scratch"**
4. Fill in the details:
   - **App Name**: `Kiitos Krab` (or whatever you prefer)
   - **Pick a workspace**: Select your workspace
5. Click **"Create App"**

## Step 2: Configure Basic Information

1. In the left sidebar, click **"Basic Information"**
2. Under **"App Credentials"**, note down:
   - **Signing Secret** (you'll need this for `SLACK_SIGNING_SECRET`)
3. Under **"Display Information"**, you can customize:
   - **App Name**: `Kiitos Krab`
   - **Short Description**: `Send kudos to team members with crab-themed enthusiasm!`
   - **App Icon**: Upload a crab emoji or image 🦀

## Step 3: Add Bot Token Scopes

1. In the left sidebar, click **"OAuth & Permissions"**
2. Scroll down to **"Scopes"** section
3. Under **"Bot Token Scopes"**, add these permissions:
   - `chat:write` - Send messages to channels
   - `commands` - Add slash commands
   - `app_mentions:read` - Read mentions of your app
   - `channels:read` - Read public channel information (required for `/kk leaderboard #channelname`)
   - `groups:read` - Read private channel information (required for `/kk leaderboard #channelname` with private channels)

4. Click **"Install to Workspace"** at the top of the page
5. After installation, copy the **"Bot User OAuth Token"** (starts with `xoxb-`) - this is your `SLACK_BOT_TOKEN`

**Note:** The `channels:read` and `groups:read` scopes are optional but required if you want to use channel names (like `#channelname`) in leaderboard commands. Without these scopes, you can still use leaderboard commands but only in the current channel.

## Step 4: Create Slash Command

1. In the left sidebar, click **"Slash Commands"**
2. Click **"Create New Command"**
3. Fill in the details:
   - **Command**: `/kk`
   - **Request URL**: 
     - For local testing: `https://your-ngrok-url.ngrok.io/slack/events`
     - For production: Your AWS Lambda endpoint
   - **Short Description**: `Send kudos to team members (supports multiple recipients)`
   - **Usage Hint**: `@user message or @user1 @user2 message`
4. **Important**: Under the slash command settings, check **"Escape channels, users, and links sent to your app"** - this ensures proper user ID format is sent to the bot
5. Click **"Save"**

## Step 5: Configure Event Subscriptions

1. In the left sidebar, click **"Event Subscriptions"**
2. Toggle **"Enable Events"** to **On**
3. Set **Request URL**:
   - For local testing: `https://your-ngrok-url.ngrok.io/slack/events`
   - For production: Your AWS Lambda endpoint
4. Wait for Slack to verify the URL (should show a green checkmark)
5. Under **"Subscribe to bot events"**, add:
   - `app_mention` - When someone mentions your app
6. Click **"Save Changes"**

## Step 6: Configure Interactivity & Shortcuts (Optional)

1. In the left sidebar, click **"Interactivity & Shortcuts"**
2. Toggle **"Interactivity"** to **On**
3. Set **Request URL**:
   - For local testing: `https://your-ngrok-url.ngrok.io/slack/events`
   - For production: Your AWS Lambda endpoint
4. Click **"Save Changes"**

## Step 7: Environment Variables Summary

After setup, you'll have these values for your `.env` file:

```bash
# From OAuth & Permissions page
SLACK_BOT_TOKEN=xoxb-your-bot-token-here

# From Basic Information page  
SLACK_SIGNING_SECRET=your-signing-secret-here


# Your Aiven PostgreSQL connection string
DATABASE_URL=postgresql://username:password@host:port/database

# Optional: customize monthly quota per channel
MONTHLY_QUOTA=10

# Optional: customize leaderboard size
LEADERBOARD_LIMIT=10

# Optional: customize bot personality
BOT_PERSONALITY=crab

# Optional: for migrating existing data (only if you have old kudos data)
SLACK_CHANNEL_ID=C1234567890
```

## Step 8: Local Testing with ngrok

1. Install ngrok:
   ```bash
   brew install ngrok  # macOS
   # or download from https://ngrok.com/
   ```

2. Start your bot locally:
   ```bash
   python run_local.py
   ```

3. In another terminal, expose localhost:
   ```bash
   ngrok http 3000
   ```

4. Copy the HTTPS URL (e.g., `https://abc123.ngrok.io`)

5. Update your Slack app configuration:
   - Go back to your Slack app settings
   - Update the Request URL in:
     - Slash Commands
     - Event Subscriptions  
     - Interactivity & Shortcuts
   - Use: `https://your-ngrok-url.ngrok.io/slack/events`

## Step 9: Test Your Bot

1. In Slack, try the slash command in any channel:
   ```
   /kk @username thanks for the help!
   ```

2. Mention the bot:
   ```
   @Kiitos Krab
   ```

3. Check the leaderboard (channel-specific):
   ```
   /kk leaderboard
   ```

4. Check your stats (channel-specific):
   ```
   /kk stats
   ```

5. Test multi-channel functionality:
   - Send kudos in #general
   - Send kudos in #engineering
   - Check that leaderboards and stats are different in each channel

## Troubleshooting

### Bot not responding to slash commands?
- Check that the Request URL is correct and verified
- Ensure the bot is installed to your workspace
- Verify the bot token has the correct scopes

### Events not working?
- Make sure Event Subscriptions are enabled
- Verify the Request URL is accessible
- Check that `app_mention` is subscribed

### Database connection issues?
- Verify your Aiven PostgreSQL connection string
- Check that the database is accessible from your IP
- Ensure the bot has proper database permissions

### ngrok issues?
- Make sure ngrok is running and the URL is accessible
- Update the Request URL in Slack app settings
- Check ngrok logs for any errors

## Production Deployment

When ready to deploy to AWS Lambda:

1. Update your Slack app Request URLs to point to your Lambda endpoint
2. Set environment variables in AWS Lambda
3. Deploy using the provided `deploy.sh` script
4. Test all functionality in production

## Security Notes

- Never commit your `.env` file to version control
- Keep your bot token and signing secret secure
- Use environment variables in production
- Regularly rotate your tokens if needed

---

**Need help?** Check the [Slack API documentation](https://api.slack.com/) or create an issue in the GitHub repository! 🦀 
