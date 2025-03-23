import os
import logging
import asyncio
import sqlite3
from utils.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def fix_database_schema():
    """
    Fix the SQLite database schema by adding missing columns.
    """
    try:
        # Initialize config
        config = Config()
        
        # Get database directory and path
        db_dir = config.get('storage.database_dir')
        db_path = os.path.join(db_dir, 'timetracker.db')
        
        logger.info(f"Fixing database schema at {db_path}")
        
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if the duration column exists in the activity_logs table
        cursor.execute("PRAGMA table_info(activity_logs)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        # Add duration column if it doesn't exist
        if 'duration' not in column_names:
            logger.info("Adding 'duration' column to activity_logs table")
            cursor.execute('''
            ALTER TABLE activity_logs
            ADD COLUMN duration INTEGER
            ''')
            logger.info("'duration' column added successfully")
        else:
            logger.info("'duration' column already exists")
        
        # Commit the changes
        conn.commit()
        
        # Close the connection
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error fixing database schema: {str(e)}")
        return False

async def main():
    success = await fix_database_schema()
    if success:
        logger.info("✅ Database schema fix completed successfully!")
    else:
        logger.error("❌ Database schema fix failed!")

if __name__ == "__main__":
    asyncio.run(main())
