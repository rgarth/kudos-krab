#!/usr/bin/env python3
"""
Migration script to add timezone column to channel_configs table
"""

import os
import psycopg2
import logging

logger = logging.getLogger(__name__)

def migrate_add_timezone():
    """Add timezone column to channel_configs table"""
    conn = None
    cursor = None
    try:
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        # Connect to database
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Check if timezone column already exists
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'channel_configs' 
            AND column_name = 'timezone'
        """)
        
        if cursor.fetchone():
            logger.info("Timezone column already exists, skipping migration")
            return
        
        # Add timezone column
        cursor.execute("""
            ALTER TABLE channel_configs 
            ADD COLUMN timezone VARCHAR(10)
        """)
        
        conn.commit()
        logger.info("Successfully added timezone column to channel_configs table")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if conn:
            conn.rollback()
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    migrate_add_timezone()
