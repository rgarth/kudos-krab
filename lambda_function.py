"""
AWS Lambda entry point for Kiitos Krab Slack Bot
"""
from kudos_bot import lambda_handler

# Export the handler for AWS Lambda
__all__ = ['lambda_handler'] 