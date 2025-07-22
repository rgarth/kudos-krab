"""
AWS Lambda entry point for Kudos Krab Slack Bot
"""
from kudos_bot import lambda_handler

# Export the handler for AWS Lambda
__all__ = ['lambda_handler'] 