# Kudos Krab 🦀

A Slack bot for recording and managing team kudos with a crab-themed twist!

## Features

- **Kudos Recording**: Send kudos to team members using `/kk` command
- **Monthly Leaderboards**: View top kudos senders and receivers for the current month
- **Personal Stats**: Check your own kudos sent and received
- **Monthly Quotas**: Configurable limits on kudos per person per month
- **PostgreSQL Backend**: Reliable data storage for all kudos records

## Commands

- `/kk @person message` - Send kudos to someone
- `/kk leaderboard` - Show monthly leaderboard
- `/kk stats` - Show your personal kudos statistics

## Architecture

- **Language**: Python (AWS Lambda compatible)
- **Database**: PostgreSQL
- **Deployment**: AWS Lambda
- **Slack Integration**: Slack Events API (write-only)

## Database Schema

```sql
CREATE TABLE kudos (
    id SERIAL PRIMARY KEY,
    sender VARCHAR(255) NOT NULL,
    receiver VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Environment Variables

- `SLACK_BOT_TOKEN` - Slack bot token
- `SLACK_SIGNING_SECRET` - Slack app signing secret
- `DATABASE_URL` - PostgreSQL connection string
- `SLACK_CHANNEL_ID` - Channel ID for kudos announcements
- `MONTHLY_QUOTA` - Maximum kudos per person per month (default: 10)

## Development

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up PostgreSQL database
4. Configure Slack app and environment variables
5. Run locally or deploy to AWS Lambda

## License

MIT License - see [LICENSE](LICENSE) file for details. 