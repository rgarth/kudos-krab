#!/usr/bin/env python3
"""
Utility script to clear kudos before a specific date from PostgreSQL.
Run this from the command line to clean up old kudos data.
"""

import os
import sys
import psycopg2
from datetime import datetime
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_connection():
    """Get a database connection"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("❌ DATABASE_URL environment variable not set!")
        sys.exit(1)
    
    try:
        return psycopg2.connect(database_url)
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        sys.exit(1)

@contextmanager
def get_db_cursor():
    """Get a database cursor with automatic cleanup"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()

def clear_kudos_before_date(cutoff_date):
    """
    Clear all kudos given before a specific date.
    
    Args:
        cutoff_date (str): Date in YYYY-MM-DD format
    """
    print(f"🦀 Clearing kudos before {cutoff_date}...")
    
    # Convert date to timestamp for comparison
    cutoff_datetime = datetime.strptime(cutoff_date, '%Y-%m-%d')
    
    with get_db_cursor() as cursor:
        # First, get count of items to be deleted
        cursor.execute("""
            SELECT COUNT(*) FROM kudos 
            WHERE timestamp < %s
        """, (cutoff_datetime,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("✅ No kudos found before that date!")
            return
        
        print(f"📊 Found {count} kudos to delete...")
        
        # Get items to be deleted for preview
        cursor.execute("""
            SELECT sender, receiver, timestamp 
            FROM kudos 
            WHERE timestamp < %s
            ORDER BY timestamp DESC
        """, (cutoff_datetime,))
        
        items = cursor.fetchall()
        
        # Show what will be deleted
        print("\n🗑️  Items to be deleted:")
        for sender, receiver, timestamp in items:
            print(f"   {timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {sender} → {receiver}")
        
        # Delete the items
        cursor.execute("""
            DELETE FROM kudos 
            WHERE timestamp < %s
        """, (cutoff_datetime,))
        
        deleted_count = cursor.rowcount
        print(f"\n✅ Done! Deleted {deleted_count} kudos before {cutoff_date} 🦀")

def clear_kudos_before_timestamp(cutoff_timestamp):
    """
    Clear all kudos given before a specific timestamp.
    
    Args:
        cutoff_timestamp (int): Unix timestamp
    """
    print(f"🦀 Clearing kudos before timestamp {cutoff_timestamp}...")
    
    # Convert timestamp to datetime
    cutoff_datetime = datetime.fromtimestamp(cutoff_timestamp)
    
    with get_db_cursor() as cursor:
        # First, get count of items to be deleted
        cursor.execute("""
            SELECT COUNT(*) FROM kudos 
            WHERE timestamp < %s
        """, (cutoff_datetime,))
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("✅ No kudos found before that timestamp!")
            return
        
        print(f"📊 Found {count} kudos to delete...")
        
        # Get items to be deleted for preview
        cursor.execute("""
            SELECT sender, receiver, timestamp 
            FROM kudos 
            WHERE timestamp < %s
            ORDER BY timestamp DESC
        """, (cutoff_datetime,))
        
        items = cursor.fetchall()
        
        # Show what will be deleted
        print("\n🗑️  Items to be deleted:")
        for sender, receiver, timestamp in items:
            print(f"   {timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {sender} → {receiver}")
        
        # Delete the items
        cursor.execute("""
            DELETE FROM kudos 
            WHERE timestamp < %s
        """, (cutoff_datetime,))
        
        deleted_count = cursor.rowcount
        print(f"\n✅ Done! Deleted {deleted_count} kudos before timestamp {cutoff_timestamp} 🦀")

def preview_kudos_before_date(cutoff_date):
    """
    Preview kudos that would be deleted without actually deleting them.
    
    Args:
        cutoff_date (str): Date in YYYY-MM-DD format
    """
    print(f"👀 Previewing kudos before {cutoff_date}...")
    print("🔍 This is a preview - no data will be deleted\n")
    
    # Convert date to timestamp for comparison
    cutoff_datetime = datetime.strptime(cutoff_date, '%Y-%m-%d')
    
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT sender, receiver, timestamp 
            FROM kudos 
            WHERE timestamp < %s
            ORDER BY timestamp DESC
        """, (cutoff_datetime,))
        
        items = cursor.fetchall()
        
        if not items:
            print("✅ No kudos found before that date!")
            return
        
        print(f"📊 Found {len(items)} kudos that would be deleted:\n")
        for sender, receiver, timestamp in items:
            print(f"📝 {timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {sender} → {receiver}")
        
        print(f"\n👀 Preview complete! {len(items)} kudos would be deleted before {cutoff_date} 🦀")

def preview_kudos_before_timestamp(cutoff_timestamp):
    """
    Preview kudos that would be deleted without actually deleting them.
    
    Args:
        cutoff_timestamp (int): Unix timestamp
    """
    print(f"👀 Previewing kudos before timestamp {cutoff_timestamp}...")
    print("🔍 This is a preview - no data will be deleted\n")
    
    # Convert timestamp to datetime
    cutoff_datetime = datetime.fromtimestamp(cutoff_timestamp)
    
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT sender, receiver, timestamp 
            FROM kudos 
            WHERE timestamp < %s
            ORDER BY timestamp DESC
        """, (cutoff_datetime,))
        
        items = cursor.fetchall()
        
        if not items:
            print("✅ No kudos found before that timestamp!")
            return
        
        print(f"📊 Found {len(items)} kudos that would be deleted:\n")
        for sender, receiver, timestamp in items:
            print(f"📝 {timestamp.strftime('%Y-%m-%d %H:%M:%S')} | {sender} → {receiver}")
        
        print(f"\n👀 Preview complete! {len(items)} kudos would be deleted before timestamp {cutoff_timestamp} 🦀")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python clear_kudos.py YYYY-MM-DD")
        print("  python clear_kudos.py now")
        print("  python clear_kudos.py --preview YYYY-MM-DD")
        print("  python clear_kudos.py --preview now")
        print("\nExamples:")
        print("  python clear_kudos.py 2024-01-01")
        print("  python clear_kudos.py now")
        print("  python clear_kudos.py --preview 2024-01-01")
        sys.exit(1)
    
    # Check for preview mode
    preview_mode = False
    if sys.argv[1] == '--preview':
        if len(sys.argv) < 3:
            print("❌ Missing date argument for --preview")
            print("Usage: python clear_kudos.py --preview YYYY-MM-DD")
            print("   or: python clear_kudos.py --preview now")
            sys.exit(1)
        preview_mode = True
        cutoff_date = sys.argv[2]
    else:
        cutoff_date = sys.argv[1]
    
    # Handle "now" option
    if cutoff_date.lower() == 'now':
        cutoff_timestamp = int(datetime.now().timestamp())
        print(f"🕐 Using current timestamp: {cutoff_timestamp}")
        
        if preview_mode:
            preview_kudos_before_timestamp(cutoff_timestamp)
        else:
            # Ask for confirmation before deleting
            print(f"⚠️  WARNING: This will permanently delete all kudos before NOW (timestamp: {cutoff_timestamp})")
            response = input("Are you sure? Type 'yes' to continue: ")
            
            if response.lower() == 'yes':
                clear_kudos_before_timestamp(cutoff_timestamp)
            else:
                print("❌ Operation cancelled")
                sys.exit(0)
    else:
        # Validate date format
        try:
            datetime.strptime(cutoff_date, '%Y-%m-%d')
        except ValueError:
            print("❌ Invalid date format! Use YYYY-MM-DD or 'now'")
            print("Examples: 2024-01-01 or now")
            sys.exit(1)
        
        if preview_mode:
            preview_kudos_before_date(cutoff_date)
        else:
            # Ask for confirmation before deleting
            print(f"⚠️  WARNING: This will permanently delete all kudos before {cutoff_date}")
            response = input("Are you sure? Type 'yes' to continue: ")
            
            if response.lower() == 'yes':
                clear_kudos_before_date(cutoff_date)
            else:
                print("❌ Operation cancelled")
                sys.exit(0) 