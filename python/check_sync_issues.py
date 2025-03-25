"""
Check synchronization issues between local database and Supabase.
"""
import asyncio
import os
import sqlite3
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def check_sync_issues():
    """Check synchronization issues."""
    try:
        # Get database path
        db_path = os.path.expanduser("~/AppData/Roaming/TimeTracker/db/timetracker.db")
        if not os.path.exists(db_path):
            logger.error(f"Database file does not exist at {db_path}")
            return
            
        logger.info(f"Connecting to local database: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check unsynchronized activity logs
        cursor.execute("SELECT COUNT(*) FROM activity_logs WHERE synced = 0")
        unsynced_activities = cursor.fetchone()[0]
        logger.info(f"Found {unsynced_activities} unsynchronized activity logs")
        
        # Show sample of unsynced activity logs
        if unsynced_activities > 0:
            cursor.execute("""
                SELECT id, window_title, process_name, start_time, end_time, synced
                FROM activity_logs
                WHERE synced = 0
                LIMIT 5
            """)
            sample_activities = cursor.fetchall()
            logger.info("Sample unsynced activity logs:")
            for activity in sample_activities:
                logger.info(f"  ID: {activity[0]}, Window: {activity[1]}, Process: {activity[2]}")
        
        # Check unsynchronized screenshots
        cursor.execute("SELECT COUNT(*) FROM screenshots WHERE synced = 0")
        unsynced_screenshots = cursor.fetchone()[0]
        logger.info(f"Found {unsynced_screenshots} unsynchronized screenshots")
        
        # Show sample of unsynced screenshots
        if unsynced_screenshots > 0:
            cursor.execute("""
                SELECT id, filepath, timestamp, synced
                FROM screenshots
                WHERE synced = 0
                LIMIT 5
            """)
            sample_screenshots = cursor.fetchall()
            logger.info("Sample unsynced screenshots:")
            for screenshot in sample_screenshots:
                logger.info(f"  ID: {screenshot[0]}, File: {screenshot[1]}")
        
        # Check organization memberships
        cursor.execute("SELECT COUNT(*) FROM org_members")
        org_members_count = cursor.fetchone()[0]
        logger.info(f"Found {org_members_count} organization memberships")
        
        if org_members_count > 0:
            cursor.execute("""
                SELECT id, org_id, user_id, role
                FROM org_members
                LIMIT 5
            """)
            org_members = cursor.fetchall()
            logger.info("Organization memberships:")
            for member in org_members:
                logger.info(f"  ID: {member[0]}, Org: {member[1]}, User: {member[2]}, Role: {member[3]}")
        
        # Check if sync_status table is working
        cursor.execute("SELECT * FROM sync_status")
        sync_statuses = cursor.fetchall()
        logger.info("Sync status records:")
        for status in sync_statuses:
            logger.info(f"  {status}")
        
        # Close connection
        conn.close()
        
    except Exception as e:
        logger.error(f"Error checking sync issues: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    print("=== Sync Issue Checker ===")
    asyncio.run(check_sync_issues())
