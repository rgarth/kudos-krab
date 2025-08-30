#!/usr/bin/env python3
"""
Migration script to add channel_id column to existing kudos table.
This script will:
1. Add the channel_id column to the kudos table
2. Set a default value for existing records (if SLACK_CHANNEL_ID is set)
3. Make the column NOT NULL after populating it
"""

import os
import sys
import psycopg2
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

def check_column_exists(cursor, table_name, column_name):
    """Check if a column exists in a table"""
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = %s AND column_name = %s
    """, (table_name, column_name))
    return cursor.fetchone() is not None

def migrate_add_channel_id():
    """Add channel_id column to kudos table"""
    print("🦀 Starting migration to add channel_id column...")
    
    with get_db_cursor() as cursor:
        # Check if channel_id column already exists
        if check_column_exists(cursor, 'kudos', 'channel_id'):
            print("✅ channel_id column already exists!")
            return
        
        print("📊 Adding channel_id column...")
        
        # Add the column as nullable first
        cursor.execute("""
            ALTER TABLE kudos 
            ADD COLUMN channel_id VARCHAR(255)
        """)
        
        # Get the default channel ID from environment
        default_channel_id = os.getenv('SLACK_CHANNEL_ID')
        
        if default_channel_id:
            print(f"🔄 Populating existing records with default channel_id: {default_channel_id}")
            cursor.execute("""
                UPDATE kudos 
                SET channel_id = %s 
                WHERE channel_id IS NULL
            """, (default_channel_id,))
            
            updated_count = cursor.rowcount
            print(f"✅ Updated {updated_count} existing records")
        else:
            print("⚠️  No SLACK_CHANNEL_ID found in environment")
            print("   Existing records will have NULL channel_id")
            print("   You may want to update them manually or delete them")
        
        # Make the column NOT NULL
        print("🔒 Making channel_id NOT NULL...")
        cursor.execute("""
            ALTER TABLE kudos 
            ALTER COLUMN channel_id SET NOT NULL
        """)
        
        # Add indexes for the new column
        print("📈 Adding indexes for channel_id...")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_kudos_channel ON kudos(channel_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_kudos_sender_channel ON kudos(sender, channel_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_kudos_receiver_channel ON kudos(receiver, channel_id)
        """)
        
        print("✅ Migration completed successfully! 🦀")

if __name__ == "__main__":
    try:
        migrate_add_channel_id()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
