import os
import json
from pathlib import Path

# Default personality
DEFAULT_PERSONALITY = "crab"

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
