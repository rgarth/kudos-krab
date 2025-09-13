import os
import json
from pathlib import Path
from config.settings import DEFAULT_PERSONALITY

def get_available_personalities():
    """Get list of available personality names from JSON files"""
    personality_dir = Path(__file__).parent.parent / "personalities"
    personalities = []
    
    if personality_dir.exists():
        for file_path in personality_dir.glob("*.json"):
            if file_path.name != "README.md":  # Skip README
                personality_name = file_path.stem
                personalities.append(personality_name)
    
    return sorted(personalities)

def load_personality(personality_name=None):
    """Load personality responses from JSON file"""
    if personality_name is None:
        personality_name = os.environ.get("BOT_PERSONALITY", DEFAULT_PERSONALITY)
    
    # Path to personality files
    personality_dir = Path(__file__).parent.parent / "personalities"
    personality_file = personality_dir / f"{personality_name}.json"
    
    # Load default personality if requested one doesn't exist
    if not personality_file.exists():
        default_file = personality_dir / f"{DEFAULT_PERSONALITY}.json"
        if default_file.exists():
            personality_file = default_file
        else:
            raise FileNotFoundError(f"Required personality file not found: {personality_file}")
    
    try:
        with open(personality_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Error loading personality {personality_name}: {e}")

def load_personality_for_channel(channel_id, db_manager):
    """Load personality for a specific channel, falling back to default if not configured"""
    try:
        config = db_manager.get_channel_config(channel_id)
        if config and config['personality_name']:
            return load_personality(config['personality_name'])
    except Exception as e:
        # Log error but don't fail - fall back to default
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to load channel-specific personality for {channel_id}: {e}")
    
    # Fall back to default personality
    return load_personality()
