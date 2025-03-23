"""
Script to reset the TimeTracker database by deleting the existing database file.
This will force the application to create a new database with the correct schema.
"""
import os
import shutil
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def reset_database():
    """Delete the existing database file to reset the schema."""
    # Path to the database file
    db_path = Path(os.path.expanduser("~")) / "AppData" / "Roaming" / "TimeTracker" / "db" / "timetracker.db"
    
    try:
        if db_path.exists():
            logger.info(f"Found database file at: {db_path}")
            
            # Create a backup just in case
            backup_path = db_path.with_suffix(".db.bak")
            shutil.copy2(db_path, backup_path)
            logger.info(f"Created backup at: {backup_path}")
            
            # Delete the file
            os.remove(db_path)
            logger.info(f"Deleted database file: {db_path}")
            print(f"✅ Successfully deleted database file: {db_path}")
            print(f"✅ Backup created at: {backup_path}")
            return True
        else:
            logger.warning(f"Database file not found at: {db_path}")
            print(f"⚠️ Database file not found at: {db_path}")
            return False
    except Exception as e:
        logger.error(f"Error resetting database: {str(e)}")
        print(f"❌ Error resetting database: {str(e)}")
        return False

if __name__ == "__main__":
    print("Resetting TimeTracker database...")
    reset_database()
    print("Done! You can now run the application again to create a fresh database.")
