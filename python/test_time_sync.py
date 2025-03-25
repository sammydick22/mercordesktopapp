"""
Test script for time entry synchronization between local database and Supabase.
"""
import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Make sure we load environment variables
load_dotenv()

async def create_test_time_entry():
    """Create a test time entry in the local database."""
    try:
        # Dynamically import services
        from services.database import DatabaseService
        
        # Import extensions to patch services with additional methods
        import services.init_service_extensions
        
        # Initialize database service
        logger.info("Creating database service...")
        db_service = DatabaseService()
        logger.info("Database service created")
        
        # Get connection to database for direct queries
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Create a unique test time entry
        entry_id = str(uuid.uuid4())
        start_time = datetime.now().isoformat()
        end_time = (datetime.now() + timedelta(hours=1)).isoformat()
        description = f"Test time entry {entry_id}"
        
        # Insert the time entry
        logger.info(f"Creating test time entry with ID: {entry_id}")
        cursor.execute(
            """
            INSERT INTO time_entries 
            (id, start_time, end_time, duration, description, is_active, synced, created_at, updated_at, user_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_id, 
                start_time, 
                end_time, 
                3600,  # 1 hour in seconds
                description,
                0,     # not active
                0,     # not synced
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                "test-user-id"  # This will be replaced by the actual user ID during sync
            )
        )
        
        # Commit the changes
        conn.commit()
        
        logger.info(f"Successfully created test time entry: {entry_id}")
        return entry_id
        
    except Exception as e:
        logger.error(f"Error creating test time entry: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

async def sync_time_entries():
    """Trigger synchronization of time entries."""
    try:
        # Dynamically import services
        from services.database import DatabaseService
        from services.supabase_auth import SupabaseAuthService
        from services.supabase_sync import SupabaseSyncService
        
        # Import extensions to patch services with additional methods
        import services.init_service_extensions
        
        # Initialize services
        logger.info("Creating services...")
        db_service = DatabaseService()
        auth_service = SupabaseAuthService()
        
        # Check if authenticated
        if not hasattr(auth_service, 'is_authenticated') or not auth_service.is_authenticated():
            # Check if we have a saved session
            session_path = os.path.expanduser("~/TimeTracker/data/session.json")
            if os.path.exists(session_path):
                logger.info("Found saved session, attempting to load...")
                if auth_service.load_session(session_path):
                    logger.info("Session loaded successfully")
                    if auth_service.is_authenticated():
                        logger.info("Session is valid")
                    else:
                        logger.error("Session is expired or invalid")
                        return False
                else:
                    logger.error("Failed to load session")
                    return False
            else:
                logger.error("No saved session found")
                return False
                
        logger.info(f"Using authenticated user: {auth_service.user.get('email')}")
        
        # Create sync service
        sync_service = SupabaseSyncService(db_service, auth_service)
        
        # Sync time entries
        logger.info("Triggering time entries sync...")
        result = await sync_service.sync_time_entries()
        
        logger.info(f"Sync completed with result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error syncing time entries: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

async def check_time_entries():
    """Check time entries in both local database and Supabase."""
    try:
        # Dynamically import services
        from services.database import DatabaseService
        from services.supabase_auth import SupabaseAuthService
        from services.supabase_sync import SupabaseSyncService
        
        # Import extensions to patch services with additional methods
        import services.init_service_extensions
        
        # Initialize services
        logger.info("Creating services...")
        db_service = DatabaseService()
        auth_service = SupabaseAuthService()
        
        # Check if authenticated
        if not hasattr(auth_service, 'is_authenticated') or not auth_service.is_authenticated():
            # Check if we have a saved session
            session_path = os.path.expanduser("~/TimeTracker/data/session.json")
            if os.path.exists(session_path):
                logger.info("Found saved session, attempting to load...")
                if auth_service.load_session(session_path):
                    logger.info("Session loaded successfully")
                    if auth_service.is_authenticated():
                        logger.info("Session is valid")
                    else:
                        logger.error("Session is expired or invalid")
                        return False
                else:
                    logger.error("Failed to load session")
                    return False
            else:
                logger.error("No saved session found")
                return False
        
        logger.info(f"Using authenticated user: {auth_service.user.get('email')}")
                
        # Create sync service
        sync_service = SupabaseSyncService(db_service, auth_service)
        
        # Get user ID
        user_id = auth_service.user.get("id")
        
        # Get time entries from the local database
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Query local time entries
        cursor.execute(
            """
            SELECT id, start_time, end_time, duration, description, is_active, synced
            FROM time_entries
            ORDER BY start_time DESC
            LIMIT 10
            """
        )
        local_entries = cursor.fetchall()
        
        logger.info(f"Found {len(local_entries)} recent time entries in local database")
        for entry in local_entries:
            logger.info(f"Local entry: id={entry[0]}, description={entry[4]}, synced={entry[6]}")
        
        # Query Supabase time entries
        result = sync_service.supabase.table("time_entries").select("*").eq("user_id", user_id).order("start_time", desc=True).limit(10).execute()
        
        supabase_entries = result.data if result and result.data else []
        
        logger.info(f"Found {len(supabase_entries)} recent time entries in Supabase")
        for entry in supabase_entries:
            logger.info(f"Supabase entry: id={entry.get('id')}, description={entry.get('description')}")
        
        # Check if time entries are correctly synchronized
        local_ids = [entry[0] for entry in local_entries]
        supabase_ids = [entry.get('id') for entry in supabase_entries]
        
        matched_ids = set(local_ids).intersection(set(supabase_ids))
        logger.info(f"Found {len(matched_ids)} matched time entries between local and Supabase")
        
        return {
            "local_entries": len(local_entries),
            "supabase_entries": len(supabase_entries),
            "matched_entries": len(matched_ids),
            "matching_percentage": (len(matched_ids) / len(local_ids) * 100) if local_ids else 0
        }
        
    except Exception as e:
        logger.error(f"Error checking time entries: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

async def run_test():
    """Run the full test sequence."""
    # Create a test time entry
    entry_id = await create_test_time_entry()
    if not entry_id:
        logger.error("Failed to create test time entry")
        return
    
    # Trigger synchronization
    sync_result = await sync_time_entries()
    if not sync_result:
        logger.error("Failed to sync time entries")
        return
    
    # Check time entries
    check_result = await check_time_entries()
    if not check_result:
        logger.error("Failed to check time entries")
        return
    
    # Print test summary
    logger.info("\n=== TEST SUMMARY ===")
    logger.info(f"Created test time entry: {entry_id}")
    logger.info(f"Sync result: {sync_result}")
    logger.info(f"Check result: {check_result}")
    
    if check_result.get("matching_percentage", 0) > 0:
        logger.info("SUCCESS: Time entries are being synchronized correctly")
    else:
        logger.info("FAILURE: Time entries are not being synchronized correctly")

if __name__ == "__main__":
    print("=== Time Entry Sync Test ===")
    asyncio.run(run_test())
