import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections with pooling for Aiven free tier (5 connection limit)"""
    
    def __init__(self):
        self.connection_pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool with minimal connections for Aiven free tier"""
        try:
            database_url = os.getenv('DATABASE_URL')
            if not database_url:
                raise ValueError("DATABASE_URL environment variable not set")
            
            # Parse connection string to get individual components
            # Format: postgresql://username:password@host:port/database or postgres://username:password@host:port/database
            if database_url.startswith('postgresql://') or database_url.startswith('postgres://'):
                # Extract components for better error handling
                self.connection_pool = pool.SimpleConnectionPool(
                    minconn=1,  # Minimum 1 connection
                    maxconn=3,  # Maximum 3 connections (leaving 2 for safety)
                    dsn=database_url
                )
                logger.info("Database connection pool initialized successfully")
            else:
                raise ValueError("Invalid DATABASE_URL format - must start with 'postgresql://' or 'postgres://'")
                
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get a database connection from the pool"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if conn:
                self.connection_pool.putconn(conn)
    
    def initialize_tables(self):
        """Create the kudos table if it doesn't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS kudos (
            id SERIAL PRIMARY KEY,
            sender VARCHAR(255) NOT NULL,
            receiver VARCHAR(255) NOT NULL,
            channel_id VARCHAR(255) NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_kudos_sender ON kudos(sender);
        CREATE INDEX IF NOT EXISTS idx_kudos_receiver ON kudos(receiver);
        CREATE INDEX IF NOT EXISTS idx_kudos_timestamp ON kudos(timestamp);
        CREATE INDEX IF NOT EXISTS idx_kudos_channel ON kudos(channel_id);
        CREATE INDEX IF NOT EXISTS idx_kudos_sender_channel ON kudos(sender, channel_id);
        CREATE INDEX IF NOT EXISTS idx_kudos_receiver_channel ON kudos(receiver, channel_id);
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(create_table_sql)
                conn.commit()
                logger.info("Database tables initialized successfully")
    
    def record_kudos(self, sender: str, receiver: str, channel_id: str) -> bool:
        """Record a new kudos entry"""
        sql = """
        INSERT INTO kudos (sender, receiver, channel_id)
        VALUES (%s, %s, %s)
        """
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (sender, receiver, channel_id))
                    conn.commit()
                    logger.info(f"Kudos recorded: {sender} -> {receiver} in channel {channel_id}")
                    return True
        except Exception as e:
            logger.error(f"Failed to record kudos: {e}")
            return False
    
    def get_monthly_kudos_count(self, user: str, month: int, year: int, channel_id: str = None) -> int:
        """Get the number of kudos sent by a user in a specific month and channel"""
        if channel_id:
            sql = """
            SELECT COUNT(*) FROM kudos 
            WHERE sender = %s 
            AND channel_id = %s
            AND EXTRACT(MONTH FROM timestamp) = %s 
            AND EXTRACT(YEAR FROM timestamp) = %s
            """
            params = (user, channel_id, month, year)
        else:
            sql = """
            SELECT COUNT(*) FROM kudos 
            WHERE sender = %s 
            AND EXTRACT(MONTH FROM timestamp) = %s 
            AND EXTRACT(YEAR FROM timestamp) = %s
            """
            params = (user, month, year)
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                result = cursor.fetchone()
                return result[0] if result else 0
    
    def get_monthly_kudos_received_count(self, user: str, month: int, year: int, channel_id: str = None) -> int:
        """Get the number of kudos received by a user in a specific month and channel"""
        if channel_id:
            sql = """
            SELECT COUNT(*) FROM kudos 
            WHERE receiver = %s 
            AND channel_id = %s
            AND EXTRACT(MONTH FROM timestamp) = %s 
            AND EXTRACT(YEAR FROM timestamp) = %s
            """
            params = (user, channel_id, month, year)
        else:
            sql = """
            SELECT COUNT(*) FROM kudos 
            WHERE receiver = %s 
            AND EXTRACT(MONTH FROM timestamp) = %s 
            AND EXTRACT(YEAR FROM timestamp) = %s
            """
            params = (user, month, year)
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                result = cursor.fetchone()
                return result[0] if result else 0
    
    def get_monthly_leaderboard(self, month: int, year: int, channel_id: str = None):
        """Get monthly leaderboard for senders and receivers in a specific channel"""
        if channel_id:
            sender_sql = """
            SELECT sender, COUNT(*) as count 
            FROM kudos 
            WHERE channel_id = %s
            AND EXTRACT(MONTH FROM timestamp) = %s 
            AND EXTRACT(YEAR FROM timestamp) = %s
            GROUP BY sender 
            ORDER BY count DESC 
            LIMIT 10
            """
            
            receiver_sql = """
            SELECT receiver, COUNT(*) as count 
            FROM kudos 
            WHERE channel_id = %s
            AND EXTRACT(MONTH FROM timestamp) = %s 
            AND EXTRACT(YEAR FROM timestamp) = %s
            GROUP BY receiver 
            ORDER BY count DESC 
            LIMIT 10
            """
            
            params = (channel_id, month, year)
        else:
            sender_sql = """
            SELECT sender, COUNT(*) as count 
            FROM kudos 
            WHERE EXTRACT(MONTH FROM timestamp) = %s 
            AND EXTRACT(YEAR FROM timestamp) = %s
            GROUP BY sender 
            ORDER BY count DESC 
            LIMIT 10
            """
            
            receiver_sql = """
            SELECT receiver, COUNT(*) as count 
            FROM kudos 
            WHERE EXTRACT(MONTH FROM timestamp) = %s 
            AND EXTRACT(YEAR FROM timestamp) = %s
            GROUP BY receiver 
            ORDER BY count DESC 
            LIMIT 10
            """
            
            params = (month, year)
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # Get top senders
                cursor.execute(sender_sql, params)
                top_senders = cursor.fetchall()
                
                # Get top receivers
                cursor.execute(receiver_sql, params)
                top_receivers = cursor.fetchall()
                
                return {
                    'senders': top_senders,
                    'receivers': top_receivers
                }
    
    def get_user_stats(self, user: str, channel_id: str = None):
        """Get kudos statistics for a specific user in a specific channel"""
        if channel_id:
            sent_sql = """
            SELECT COUNT(*) FROM kudos WHERE sender = %s AND channel_id = %s
            """
            
            received_sql = """
            SELECT COUNT(*) FROM kudos WHERE receiver = %s AND channel_id = %s
            """
            
            monthly_sent_sql = """
            SELECT COUNT(*) FROM kudos 
            WHERE sender = %s 
            AND channel_id = %s
            AND EXTRACT(MONTH FROM timestamp) = EXTRACT(MONTH FROM CURRENT_DATE)
            AND EXTRACT(YEAR FROM timestamp) = EXTRACT(YEAR FROM CURRENT_DATE)
            """
            
            params = (user, channel_id)
        else:
            sent_sql = """
            SELECT COUNT(*) FROM kudos WHERE sender = %s
            """
            
            received_sql = """
            SELECT COUNT(*) FROM kudos WHERE receiver = %s
            """
            
            monthly_sent_sql = """
            SELECT COUNT(*) FROM kudos 
            WHERE sender = %s 
            AND EXTRACT(MONTH FROM timestamp) = EXTRACT(MONTH FROM CURRENT_DATE)
            AND EXTRACT(YEAR FROM timestamp) = EXTRACT(YEAR FROM CURRENT_DATE)
            """
            
            params = (user,)
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sent_sql, params)
                total_sent = cursor.fetchone()[0]
                
                cursor.execute(received_sql, params)
                total_received = cursor.fetchone()[0]
                
                cursor.execute(monthly_sent_sql, params)
                monthly_sent = cursor.fetchone()[0]
                
                return {
                    'total_sent': total_sent,
                    'total_received': total_received,
                    'monthly_sent': monthly_sent
                }
    
    def close(self):
        """Close the connection pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Database connection pool closed")

# Global database manager instance
db_manager = None

def get_db_manager():
    """Get the global database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
        db_manager.initialize_tables()
    return db_manager 