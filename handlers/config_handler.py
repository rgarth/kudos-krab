import logging
import os
from config.personalities import get_available_personalities, load_personality_for_channel, load_personality
from config.settings import MONTHLY_QUOTA, DEFAULT_PERSONALITY, LEADERBOARD_LIMIT

logger = logging.getLogger(__name__)

def handle_config_command(ack, command, client, db_manager):
    """Handle the /kk config command to open configuration modal"""
    ack()
    
    channel_id = command.get('channel_id')
    user_id = command.get('user_id')
    trigger_id = command.get('trigger_id')
    
    # Get current channel configuration
    current_config = db_manager.get_channel_config(channel_id)
    
    # Get available personalities
    available_personalities = get_available_personalities()
    
    # Build personality options for dropdown
    personality_options = []
    for personality in available_personalities:
        personality_options.append({
            "text": {
                "type": "plain_text",
                "text": personality.title()
            },
            "value": personality
        })
    
    # Build timezone options for dropdown
    timezone_options = []
    for offset in range(-12, 15):  # UTC-12 to UTC+14
        if offset == 0:
            timezone_options.append({
                "text": {
                    "type": "plain_text",
                    "text": "UTC"
                },
                "value": "UTC"
            })
        elif offset > 0:
            timezone_options.append({
                "text": {
                    "type": "plain_text",
                    "text": f"UTC+{offset}"
                },
                "value": f"UTC+{offset}"
            })
        else:
            timezone_options.append({
                "text": {
                    "type": "plain_text",
                    "text": f"UTC{offset}"
                },
                "value": f"UTC{offset}"
            })
    
    # Set current values
    current_personality = current_config['personality_name'] if current_config else DEFAULT_PERSONALITY
    current_quota = current_config['monthly_quota'] if current_config else MONTHLY_QUOTA
    current_limit = current_config['leaderboard_limit'] if current_config else LEADERBOARD_LIMIT
    current_timezone = current_config['timezone'] if current_config else os.getenv('TIMEZONE', 'UTC')
    override_channel_id = current_config['leaderboard_channel_id'] if current_config else ""
    
    # Check if channel override is active
    has_override = bool(override_channel_id)
    
    # Build blocks dynamically based on override status
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"Configure kudos settings for <#{channel_id}>"
            }
        },
        {
            "type": "divider"
        }
    ]
    
    # Add personality block
    if not has_override:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Personality*"
            },
            "accessory": {
                "type": "static_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select personality"
                },
                "options": personality_options,
                "action_id": "personality_select",
                "initial_option": next(
                    (opt for opt in personality_options if opt["value"] == current_personality),
                    None
                )
            }
        })
        
        # Add personality description block (will be updated dynamically)
        try:
            current_personality_data = load_personality(current_personality)
            if current_personality_data and 'description' in current_personality_data:
                description_text = current_personality_data['description']
            else:
                description_text = "No description available"
        except Exception as e:
            logger.warning(f"Could not load description for current personality {current_personality}: {e}")
            description_text = "No description available"
        
        blocks.append({
            "type": "context",
            "block_id": "personality_description",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"_{description_text}_"
                }
            ]
        })
    else:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Personality*\n_Disabled - inherited from source channel_"
            }
        })
    
    # Add quota block
    if not has_override:
        blocks.append({
            "type": "input",
            "block_id": "quota_block",
            "element": {
                "type": "plain_text_input",
                "action_id": "quota_input",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Enter monthly quota"
                },
                "initial_value": str(current_quota) if current_quota is not None else ""
            },
            "label": {
                "type": "plain_text",
                "text": "Monthly Quota"
            }
        })
    else:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Monthly Quota*\n_Disabled - inherited from source channel_"
            }
        })
    
    # Add leaderboard limit block
    if not has_override:
        blocks.append({
            "type": "input",
            "block_id": "limit_block",
            "element": {
                "type": "plain_text_input",
                "action_id": "limit_input",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Enter leaderboard limit"
                },
                "initial_value": str(current_limit) if current_limit is not None else ""
            },
            "label": {
                "type": "plain_text",
                "text": "Leaderboard Limit"
            },
            "hint": {
                "type": "plain_text",
                "text": f"Number of users to show in leaderboards (default: {LEADERBOARD_LIMIT})"
            }
        })
    else:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Leaderboard Limit*\n_Disabled - inherited from source channel_"
            }
        })
    
    # Add timezone block
    if not has_override:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Timezone*"
            },
            "accessory": {
                "type": "static_select",
                "placeholder": {
                    "type": "plain_text",
                    "text": "Select timezone"
                },
                "options": timezone_options,
                "action_id": "timezone_select",
                "initial_option": next(
                    (opt for opt in timezone_options if opt["value"] == current_timezone),
                    timezone_options[12]  # Default to UTC if not found (UTC is at index 12)
                )
            }
        })
    else:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Timezone*\n_Disabled - inherited from source channel_"
            }
        })
    
    # Add leaderboard block
    blocks.append({
        "type": "input",
        "block_id": "leaderboard_block",
        "element": {
            "type": "plain_text_input",
            "action_id": "leaderboard_input",
            "placeholder": {
                "type": "plain_text",
                "text": "Channel ID (e.g., C1234567890)"
            },
            "initial_value": override_channel_id if override_channel_id else ""
        },
        "label": {
            "type": "plain_text",
            "text": "Use Another Channel's Leaderboard"
        },
        "hint": {
            "type": "plain_text",
            "text": "Enter a channel ID to use that channel's leaderboard instead of this one. This channel will inherit all settings from the source channel."
        },
        "optional": True
    })
    
    # Add help text
    blocks.extend([
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "💡 Leave empty to use this channel's leaderboard"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*How to find a Channel ID:*\n• Right-click on a channel name → 'Channel details'\n• Channel ID is listed with a copy button\n• Or right-click → 'Copy link' and extract ID from URL\n\n*Example:* Use `C1234567890` or `G010BMGBNCA`"
            }
        }
    ])
    
    # Create the modal
    modal = {
        "type": "modal",
        "callback_id": "config_modal",
        "title": {
            "type": "plain_text",
            "text": "Kudos Bot Configuration"
        },
        "submit": {
            "type": "plain_text",
            "text": "Save"
        },
        "close": {
            "type": "plain_text",
            "text": "Cancel"
        },
        "blocks": blocks
    }
    
    # Add channel_id to private metadata for the modal submission
    modal["private_metadata"] = channel_id
    
    try:
        client.views_open(
            trigger_id=trigger_id,
            view=modal
        )
    except Exception as e:
        logger.error(f"Failed to open config modal: {e}")

def handle_config_modal_submission(ack, body, client, db_manager):
    """Handle configuration modal submission"""
    ack()
    
    channel_id = body['view']['private_metadata']
    values = body['view']['state']['values']
    
    # Extract values from the modal
    personality = None
    quota = None
    leaderboard_limit = None
    timezone = None
    leaderboard_channel = None
    
    # Get personality selection - need to find the block with the select
    for block_id, block_values in values.items():
        if 'personality_select' in block_values:
            personality = block_values['personality_select']['selected_option']['value']
        elif 'quota_input' in block_values:
            try:
                quota = int(block_values['quota_input']['value'])
            except (ValueError, KeyError):
                quota = None
        elif 'limit_input' in block_values:
            try:
                leaderboard_limit = int(block_values['limit_input']['value'])
            except (ValueError, KeyError):
                leaderboard_limit = None
        elif 'timezone_select' in block_values:
            timezone = block_values['timezone_select']['selected_option']['value']
        elif 'leaderboard_input' in block_values:
            leaderboard_value = block_values['leaderboard_input']['value']
            if leaderboard_value:
                leaderboard_channel = leaderboard_value.strip()
                if not leaderboard_channel:
                    leaderboard_channel = None
            else:
                leaderboard_channel = None
    
    # If channel override is set, ignore personality, quota, limit, and timezone (they're inherited)
    if leaderboard_channel:
        personality = None
        quota = None
        leaderboard_limit = None
        timezone = None
    
    # Save configuration
    success = db_manager.save_channel_config(
        channel_id=channel_id,
        personality_name=personality,
        monthly_quota=quota,
        leaderboard_channel_id=leaderboard_channel,
        leaderboard_limit=leaderboard_limit,
        timezone=timezone
    )
    
    if success:
        # Send private confirmation message to user
        user_id = body['user']['id']
        personality_name = personality or DEFAULT_PERSONALITY
        quota_text = f"{quota}" if quota else str(MONTHLY_QUOTA)
        limit_text = f"{leaderboard_limit}" if leaderboard_limit else str(LEADERBOARD_LIMIT)
        timezone_text = timezone or os.getenv('TIMEZONE', 'UTC')
        leaderboard_text = f"<#{leaderboard_channel}>" if leaderboard_channel else "this channel"
        
        message = f"""✅ *Configuration saved for <#{channel_id}>*

• *Personality:* {personality_name.title()}
• *Monthly Quota:* {quota_text}
• *Leaderboard Limit:* {limit_text}
• *Timezone:* {timezone_text}
• *Leaderboard:* {leaderboard_text}

Settings will take effect immediately! 🦀"""
        
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text=message
        )
    else:
        # Send private error message to user
        user_id = body['user']['id']
        client.chat_postEphemeral(
            channel=channel_id,
            user=user_id,
            text="❌ Failed to save configuration. Please try again."
        )

def show_current_config(respond, channel_id, db_manager):
    """Show current channel configuration"""
    config = db_manager.get_channel_config(channel_id)
    
    if not config:
        respond("No custom configuration set for this channel. Using default settings.")
        return
    
    personality_name = config['personality_name'] or DEFAULT_PERSONALITY
    quota = config['monthly_quota'] or MONTHLY_QUOTA
    limit = config['leaderboard_limit'] or LEADERBOARD_LIMIT
    timezone = config['timezone'] or os.getenv('TIMEZONE', 'UTC')
    leaderboard_channel = config['leaderboard_channel_id'] or "this channel"
    
    if leaderboard_channel != "this channel":
        # Channel override is set - show inherited settings
        source_config = db_manager.get_channel_config(leaderboard_channel)
        if source_config:
            inherited_personality = source_config['personality_name'] or DEFAULT_PERSONALITY
            inherited_quota = source_config['monthly_quota'] or MONTHLY_QUOTA
            inherited_limit = source_config['leaderboard_limit'] or LEADERBOARD_LIMIT
            inherited_timezone = source_config['timezone'] or os.getenv('TIMEZONE', 'UTC')
        else:
            inherited_personality = DEFAULT_PERSONALITY
            inherited_quota = MONTHLY_QUOTA
            inherited_limit = LEADERBOARD_LIMIT
            inherited_timezone = os.getenv('TIMEZONE', 'UTC')
        
        message = f"""📋 *Current Configuration for <#{channel_id}>*

🔄 *Channel Override Active*
• *Leaderboard:* <#{leaderboard_channel}>
• *Personality:* {inherited_personality.title()} (inherited from <#{leaderboard_channel}>)
• *Monthly Quota:* {inherited_quota} (inherited from <#{leaderboard_channel}>)
• *Leaderboard Limit:* {inherited_limit} (inherited from <#{leaderboard_channel}>)
• *Timezone:* {inherited_timezone} (inherited from <#{leaderboard_channel}>)

Use `/kk config edit` to modify these settings."""
    else:
        # Normal configuration
        message = f"""📋 *Current Configuration for <#{channel_id}>*

• *Personality:* {personality_name.title()}
• *Monthly Quota:* {quota}
• *Leaderboard Limit:* {limit}
• *Timezone:* {timezone}
• *Leaderboard:* {leaderboard_channel}

Use `/kk config edit` to modify these settings."""
    
    respond(message)

def reset_config_to_defaults(respond, channel_id, db_manager):
    """Reset channel configuration to defaults by deleting the config"""
    try:
        # Delete the channel configuration to reset to defaults
        success = db_manager.delete_channel_config(channel_id)
        
        if success:
            respond("✅ Configuration reset to defaults for this channel. Using global settings.")
        else:
            respond("❌ Failed to reset configuration. Please try again.")
    except Exception as e:
        logger.error(f"Error resetting config for {channel_id}: {e}")
        respond("❌ Failed to reset configuration. Please try again.")

def handle_personality_select(ack, body, client, db_manager):
    """Handle personality dropdown selection and update description dynamically"""
    ack()
    
    try:
        # Get the selected personality
        selected_personality = body['actions'][0]['selected_option']['value']
        
        # Load the personality data to get description
        personality_data = load_personality(selected_personality)
        description_text = personality_data.get('description', 'No description available') if personality_data else 'No description available'
        
        # Get the current view
        view = body['view']
        
        # Update the description block
        updated_blocks = []
        for block in view['blocks']:
            if block.get('block_id') == 'personality_description':
                # Update the description block
                updated_blocks.append({
                    "type": "context",
                    "block_id": "personality_description",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"_{description_text}_"
                        }
                    ]
                })
            else:
                # Keep other blocks unchanged
                updated_blocks.append(block)
        
        # Update the view
        client.views_update(
            view_id=body['view']['id'],
            view={
                "type": "modal",
                "callback_id": "config_modal",
                "title": view['title'],
                "blocks": updated_blocks,
                "submit": view.get('submit'),
                "close": view.get('close'),
                "private_metadata": view.get('private_metadata', '')
            }
        )
        
    except Exception as e:
        logger.error(f"Error updating personality description: {e}")
