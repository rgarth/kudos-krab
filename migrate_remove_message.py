#!/usr/bin/env python3
"""
Database migration script to remove the message column from kudos table
"""
import os
import logging
from dotenv import load_dotenv
from database import get_db_manager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_remove_message():
    """Remove the message column from the kudos table"""
    db_manager = get_db_manager()
    
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Check if message column exists
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'kudos' AND column_name = 'message'
                """)
                
                if cursor.fetchone():
                    logger.info("Message column exists, removing it...")
                    
                    # Remove the message column
                    cursor.execute("ALTER TABLE kudos DROP COLUMN message")
                    conn.commit()
                    logger.info("✅ Successfully removed message column from kudos table")
                else:
                    logger.info("Message column does not exist, no migration needed")
                
                # Verify the new schema
                cursor.execute("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'kudos' 
                    ORDER BY ordinal_position
                """)
                
                columns = cursor.fetchall()
                logger.info("Current kudos table schema:")
                for column_name, data_type in columns:
                    logger.info(f"  - {column_name}: {data_type}")
                    
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == "__main__":
    print("🦀 Starting database migration to remove message column...")
    migrate_remove_message()
    print("✅ Migration completed successfully!")
