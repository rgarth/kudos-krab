import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import logging
from config.settings import LEADERBOARD_LIMIT

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections with pooling for Aiven free tier (5 connection limit)"""
    
    def __init__(self):
        self.connection_pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize connection pool with connection limits suitable for multi-channel usage"""
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
                    maxconn=10,  # Maximum 10 connections for multi-channel support
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
        """Create the kudos and channel_configs tables if they don't exist"""
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS kudos (
            id SERIAL PRIMARY KEY,
            sender VARCHAR(255) NOT NULL,
            receiver VARCHAR(255) NOT NULL,
            channel_id VARCHAR(255) NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS channel_configs (
            channel_id VARCHAR(255) PRIMARY KEY,
            personality_name VARCHAR(255),
            monthly_quota INTEGER,
            leaderboard_channel_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_kudos_sender ON kudos(sender);
        CREATE INDEX IF NOT EXISTS idx_kudos_receiver ON kudos(receiver);
        CREATE INDEX IF NOT EXISTS idx_kudos_timestamp ON kudos(timestamp);
        CREATE INDEX IF NOT EXISTS idx_kudos_channel ON kudos(channel_id);
        CREATE INDEX IF NOT EXISTS idx_kudos_sender_channel ON kudos(sender, channel_id);
        CREATE INDEX IF NOT EXISTS idx_kudos_receiver_channel ON kudos(receiver, channel_id);
        CREATE INDEX IF NOT EXISTS idx_channel_configs_leaderboard ON channel_configs(leaderboard_channel_id);
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
            LIMIT %s
            """
            
            receiver_sql = """
            SELECT receiver, COUNT(*) as count 
            FROM kudos 
            WHERE channel_id = %s
            AND EXTRACT(MONTH FROM timestamp) = %s 
            AND EXTRACT(YEAR FROM timestamp) = %s
            GROUP BY receiver 
            ORDER BY count DESC 
            LIMIT %s
            """
            
            params = (channel_id, month, year, LEADERBOARD_LIMIT)
        else:
            sender_sql = """
            SELECT sender, COUNT(*) as count 
            FROM kudos 
            WHERE EXTRACT(MONTH FROM timestamp) = %s 
            AND EXTRACT(YEAR FROM timestamp) = %s
            GROUP BY sender 
            ORDER BY count DESC 
            LIMIT %s
            """
            
            receiver_sql = """
            SELECT receiver, COUNT(*) as count 
            FROM kudos 
            WHERE EXTRACT(MONTH FROM timestamp) = %s 
            AND EXTRACT(YEAR FROM timestamp) = %s
            GROUP BY receiver 
            ORDER BY count DESC 
            LIMIT %s
            """
            
            params = (month, year, LEADERBOARD_LIMIT)
        
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
    
    def get_channel_config(self, channel_id: str):
        """Get configuration for a specific channel"""
        sql = """
        SELECT personality_name, monthly_quota, leaderboard_channel_id, created_at, updated_at
        FROM channel_configs 
        WHERE channel_id = %s
        """
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (channel_id,))
                result = cursor.fetchone()
                if result:
                    return {
                        'personality_name': result[0],
                        'monthly_quota': result[1],
                        'leaderboard_channel_id': result[2],
                        'created_at': result[3],
                        'updated_at': result[4]
                    }
                return None
    
    def save_channel_config(self, channel_id: str, personality_name: str = None, 
                           monthly_quota: int = None, leaderboard_channel_id: str = None):
        """Save or update channel configuration using UPSERT"""
        sql = """
        INSERT INTO channel_configs (channel_id, personality_name, monthly_quota, leaderboard_channel_id, created_at, updated_at)
        VALUES (%s, %s, %s, %s, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ON CONFLICT (channel_id) 
        DO UPDATE SET 
            personality_name = COALESCE(EXCLUDED.personality_name, channel_configs.personality_name),
            monthly_quota = COALESCE(EXCLUDED.monthly_quota, channel_configs.monthly_quota),
            leaderboard_channel_id = COALESCE(EXCLUDED.leaderboard_channel_id, channel_configs.leaderboard_channel_id),
            updated_at = CURRENT_TIMESTAMP
        """
        params = (channel_id, personality_name, monthly_quota, leaderboard_channel_id)
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, params)
                    conn.commit()
                    logger.info(f"Channel config saved for {channel_id}: personality={personality_name}, quota={monthly_quota}, leaderboard={leaderboard_channel_id}")
                    return True
        except Exception as e:
            logger.error(f"Failed to save channel config: {e}")
            return False
    
    def get_effective_leaderboard_channel(self, channel_id: str):
        """Get the effective leaderboard channel for a given channel (handles overrides)"""
        config = self.get_channel_config(channel_id)
        if config and config['leaderboard_channel_id']:
            return config['leaderboard_channel_id']
        return channel_id
    
    def delete_channel_config(self, channel_id: str):
        """Delete channel configuration to reset to defaults"""
        sql = "DELETE FROM channel_configs WHERE channel_id = %s"
        
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, (channel_id,))
                    conn.commit()
                    logger.info(f"Channel config deleted for {channel_id}")
                    return True
        except Exception as e:
            logger.error(f"Failed to delete channel config: {e}")
            return False
    
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