# Kudos Krab 🦀

A Slack bot for recording and managing team kudos with a crab-themed twist!

## Features

- **Kudos Recording**: Send kudos to team members using `/kk` command
- **Monthly Leaderboards**: View top kudos senders and receivers for the current month
- **Personal Stats**: Check your own kudos sent and received
- **Monthly Quotas**: Configurable limits on kudos per person per month
- **PostgreSQL Backend**: Reliable data storage for all kudos records
- **Connection Pooling**: Optimized for Aiven free tier (5 connection limit)

## Commands

- `/kk @person message` - Send kudos to someone
- `/kk @person1 @person2 message` - Send kudos to multiple people (costs multiple quota)
- `/kk leaderboard` - Show monthly leaderboard
- `/kk stats` - Show your personal kudos statistics

## Architecture

- **Language**: Python (AWS Lambda compatible)
- **Database**: PostgreSQL (Aiven free tier)
- **Deployment**: AWS Lambda
- **Slack Integration**: Slack Events API (write-only)
- **Connection Pooling**: Efficient database connection management

## Database Setup (Aiven)

1. Create a free PostgreSQL database on [Aiven](https://aiven.io/)
2. Note the connection details from the Aiven console
3. The bot will automatically create the required tables on first run

### Database Schema

```sql
CREATE TABLE kudos (
    id SERIAL PRIMARY KEY,
    sender VARCHAR(255) NOT NULL,
    receiver VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_kudos_sender ON kudos(sender);
CREATE INDEX idx_kudos_receiver ON kudos(receiver);
CREATE INDEX idx_kudos_timestamp ON kudos(timestamp);
```

### Connection Pooling

The bot uses connection pooling optimized for Aiven's free tier:
- **Min connections**: 1
- **Max connections**: 3 (leaving 2 connections for safety)
- **Automatic connection management**: Connections are properly returned to the pool

## Environment Variables

- `SLACK_BOT_TOKEN` - Slack bot token
- `SLACK_SIGNING_SECRET` - Slack app signing secret
- `DATABASE_URL` - PostgreSQL connection string (Aiven format)
- `SLACK_CHANNEL_ID` - Channel ID for kudos announcements
- `MONTHLY_QUOTA` - Maximum kudos per person per month (default: 10)

## Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up Aiven PostgreSQL database
4. Configure Slack app and environment variables
5. Run locally: `python kudos_bot.py`

## Deployment

1. Run the deployment script: `./deploy.sh`
2. Upload `kudos-krab-lambda.zip` to AWS Lambda
3. Set handler to: `lambda_function.lambda_handler`
4. Configure environment variables
5. Set timeout to 30 seconds
6. Configure Slack Events API endpoint

## Slack App Configuration

1. Create a new Slack app at https://api.slack.com/apps
2. Add slash command `/kk` with description "Send kudos to team members (supports multiple recipients)"
3. Configure Events API subscription for `app_mention`
4. Install app to workspace
5. Copy bot token and signing secret to environment variables

## License

MIT License - see [LICENSE](LICENSE) file for details. 