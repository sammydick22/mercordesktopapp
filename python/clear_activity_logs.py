"""
Clear all activity logs from the local database.
"""
import logging
import sqlite3
import os
from utils.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_database_connection():
    """Get a connection to the SQLite database."""
    config = Config()
    db_dir = config.get("storage.database_dir")
    if not db_dir:
        db_dir = os.path.join(config.get_app_dir(), "db")
    
    db_path = os.path.join(db_dir, "timetracker.db")
    logger.info(f"Connecting to database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    return conn

def clear_activity_logs():
    """Clear all activity logs from the database."""
    conn = get_database_connection()
    
    try:
        cursor = conn.cursor()
        
        # First, count how many logs we have
        cursor.execute("SELECT COUNT(*) FROM activity_logs")
        count = cursor.fetchone()[0]
        logger.info(f"Found {count} activity logs to remove")
        
        # Delete all activity logs
        cursor.execute("DELETE FROM activity_logs")
        
        # Reset the SQLite autoincrement counter (SQLite-specific)
        cursor.execute("DELETE FROM sqlite_sequence WHERE name='activity_logs'")
        
        # Commit the changes
        conn.commit()
        
        logger.info(f"Successfully removed {count} activity logs")
        return count
        
    except Exception as e:
        logger.error(f"Error clearing activity logs: {str(e)}")
        conn.rollback()
        return 0
        
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("=== CLEARING ACTIVITY LOGS ===")
    count = clear_activity_logs()
    logger.info(f"=== CLEARED {count} ACTIVITY LOGS ===")
