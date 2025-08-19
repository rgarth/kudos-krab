import re
from datetime import date
from calendar import month_name, month_abbr


def parse_month_year(text):
    """Parse month and year from text input"""
    if not text:
        return None, None
    
    text = text.strip().lower()
    parts = text.split()
    
    # Initialize variables
    month = None
    year = None
    
    # Create month mappings
    month_map = {}
    for i in range(1, 13):
        # Full month names
        month_map[month_name[i].lower()] = i
        # Three letter abbreviations
        month_map[month_abbr[i].lower()] = i
        # Numeric months
        month_map[str(i)] = i
        month_map[f"{i:02d}"] = i
    
    # Parse parts
    for part in parts:
        part = part.strip()
        
        # Check if it's a month
        if part in month_map:
            month = month_map[part]
        # Check if it's a year (4 digits)
        elif re.match(r'^\d{4}$', part):
            year = int(part)
        # Check if it's a 2-digit year (assume 20xx)
        elif re.match(r'^\d{2}$', part):
            year = 2000 + int(part)
    
    return month, year


def get_target_date(month, year):
    """Get the target date for the leaderboard"""
    today = date.today()
    
    if month is None and year is None:
        # Default to current month
        return today.month, today.year
    
    if month is None:
        # Year specified but no month - use current month
        month = today.month
    
    if year is None:
        # Month specified but no year - find the most recent occurrence
        target_year = today.year
        target_date = date(target_year, month, 1)
        
        # If this month hasn't happened yet this year, go back to last year
        if target_date > today:
            target_year = today.year - 1
        
        return month, target_year
    
    return month, year
