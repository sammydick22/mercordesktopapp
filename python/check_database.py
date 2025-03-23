import os
import logging
import sqlite3
from utils.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_database():
    """
    Check if the database exists and is properly set up.
    """
    print("Starting database check...")
    try:
        # Initialize config
        config = Config()
        
        # Get database directory and path
        db_dir = config.get('storage.database_dir')
        db_path = os.path.join(db_dir, 'timetracker.db')
        
        print(f"Database path: {db_path}")
        logger.info(f"Database path: {db_path}")
        
        # Check if database file exists
        if os.path.exists(db_path):
            file_size = os.path.getsize(db_path)
            print(f"✅ Database file exists, size: {file_size} bytes")
            logger.info(f"Database file exists, size: {file_size} bytes")
            
            # Connect to database and check tables
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            table_names = [table[0] for table in tables]
            print(f"✅ Database tables: {table_names}")
            logger.info(f"Database tables: {table_names}")
            
            # Check rows in each table
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                
                print(f"  - Table {table_name} has {row_count} rows")
                logger.info(f"Table {table_name} has {row_count} rows")
                
            # Close connection
            conn.close()
            
            print("Database check completed successfully!")
            return True
        else:
            print(f"❌ Database file does not exist at {db_path}")
            logger.error(f"Database file does not exist at {db_path}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking database: {str(e)}")
        logger.error(f"Error checking database: {str(e)}")
        return False

if __name__ == "__main__":
    success = check_database()
    print(f"\nDatabase check {'passed' if success else 'failed'}")
