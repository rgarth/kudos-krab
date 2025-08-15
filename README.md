# Kudos Krab 🦀

An overly enthusiastic Slack bot for recording team kudos

## Features

- **Record Kudos**: `/kk Thanks @user for the awesome help!` 
- **Multi-Recipient**: `/kk Great work @user1 @user2 @user3!` (costs 3 kudos)
- **Monthly Leaderboard**: `/kk leaderboard` - Top senders and top 10 receivers
- **Personal Stats**: `/kk stats` - Your sent/received kudos
- **Monthly Quota**: 10 kudos per person per month (configurable)
- **Bot Personality**: Overly enthusiastic with crab/ocean puns and familiar terms like "buddy", "friend"

## Commands

- `/kk @user message` - Send kudos to someone
- `/kk @user1 @user2 message` - Send kudos to multiple people
- `/kk leaderboard` - Show monthly leaderboard
- `/kk stats` - Show your personal stats
- `/kk help` - Show help message

## Architecture

- **Runtime**: Python 3.11
- **Framework**: Slack Bolt
- **Database**: PostgreSQL (Aiven free tier with connection pooling)
- **Deployment**: AWS Lambda OR Docker container
- **Response Time**: Sub-second for immediate feedback

## Database Schema

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

## Environment Variables

Copy `env.example` to `.env` and configure:

```bash
cp env.example .env
```

Required variables:
- `SLACK_BOT_TOKEN` - Your Slack bot token
- `SLACK_SIGNING_SECRET` - Your Slack app signing secret
- `SLACK_CHANNEL_ID` - Channel ID for kudos announcements
- `DATABASE_URL` - PostgreSQL connection string (Aiven format: `postgres://username:password@host:port/database?sslmode=require`)
- `MONTHLY_QUOTA` - Kudos quota per person per month (default: 10)
- `SLACK_BOT_USER_ID` - Bot's Slack user ID (found by right-clicking bot in Slack)

## Deployment Options

### Option 1: AWS Lambda (Recommended for Production)

**Fast response times (~100-500ms) for immediate feedback**

1. **Build Lambda package**:
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```

2. **Deploy to AWS Lambda**:
   - Upload `kudos-krab-lambda.zip`
   - Set environment variables
   - Configure API Gateway trigger

### Option 2: Docker Container

**Flexible deployment for any environment**

1. **Build and run locally**:
   ```bash
   # Build image
   docker build -t kudos-krab .
   
   # Run with environment variables
   docker run -p 3000:3000 --env-file .env kudos-krab
   ```

2. **Using Docker Compose**:
   ```bash
   docker-compose up --build
   ```

3. **Deploy to any container platform**:
   - AWS ECS/Fargate
   - Google Cloud Run
   - Azure Container Instances
   - Kubernetes
   - Heroku

## Local Development

### Prerequisites

- Python 3.11+
- PostgreSQL database (Aiven free tier recommended)
- Slack app configured (see `SLACK_SETUP.md`)
- ngrok for local testing

### Setup

1. **Clone and setup**:
   ```bash
   git clone <your-repo>
   cd kudos-krab
   cp env.example .env
   # Edit .env with your values
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run locally**:
   ```bash
   # Option 1: Direct Python
   python run_local.py
   
   # Option 2: Docker
   docker-compose up --build
   ```

4. **Expose to Slack**:
   ```bash
   ngrok http 3000
   # Update Slack app Request URL to: https://your-ngrok-url.ngrok.io/slack/events
   ```

## Database Utilities

### Clear Old Kudos

```bash
# Preview kudos before a date
python clear_kudos.py --preview 2024-01-01

# Clear kudos before a date
python clear_kudos.py 2024-01-01

# Clear kudos before now (current timestamp)
python clear_kudos.py now
```

## Slack App Setup

See `SLACK_SETUP.md` for detailed Slack app configuration instructions.

## License

MIT License - see `LICENSE` file.

---
