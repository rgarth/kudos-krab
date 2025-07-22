#!/bin/bash

# Kudos Krab AWS Lambda Deployment Script

set -e

echo "🦀 Deploying Kudos Krab to AWS Lambda..."

# Create deployment directory
DEPLOY_DIR="deployment"
rm -rf $DEPLOY_DIR
mkdir -p $DEPLOY_DIR

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt -t $DEPLOY_DIR

# Copy source files
echo "Copying source files..."
cp *.py $DEPLOY_DIR/

# Create deployment package
echo "Creating deployment package..."
cd $DEPLOY_DIR
zip -r ../kudos-krab-lambda.zip .
cd ..

# Clean up
rm -rf $DEPLOY_DIR

echo "✅ Deployment package created: kudos-krab-lambda.zip"
echo ""
echo "Next steps:"
echo "1. Upload kudos-krab-lambda.zip to AWS Lambda"
echo "2. Set handler to: lambda_function.lambda_handler"
echo "3. Configure environment variables:"
echo "   - SLACK_BOT_TOKEN"
echo "   - SLACK_SIGNING_SECRET"
echo "   - DATABASE_URL"
echo "   - SLACK_CHANNEL_ID"
echo "   - MONTHLY_QUOTA (optional, default: 10)"
echo "4. Set timeout to 30 seconds"
echo "5. Configure Slack Events API endpoint" 