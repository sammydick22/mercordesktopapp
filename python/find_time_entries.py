"""
Find time entries (activity logs) in both local database and Supabase.
"""
import asyncio
import logging
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Make sure we load environment variables
load_dotenv()

async def find_time_entries():
    """Find time entries in local database and Supabase."""
    try:
        # Dynamically import services
        from services.database import DatabaseService
        from services.supabase_auth import SupabaseAuthService
        from services.supabase_sync import SupabaseSyncService
        
        # Import extensions to patch the services with additional methods
        import services.init_service_extensions
        
        # Initialize database service
        logger.info("Creating database service...")
        db_service = DatabaseService()
        logger.info("Database service created")
        
        # Initialize auth service
        logger.info("Creating Supabase auth service...")
        auth_service = SupabaseAuthService()
        logger.info("Auth service created")
        
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
        
        # Create sync service for Supabase queries
        logger.info("Creating Supabase sync service...")
        sync_service = SupabaseSyncService(db_service, auth_service)
        logger.info("Sync service created")
        
        # 1. Query local database for all time entries (activity logs)
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        logger.info("Querying local database for all time entries...")
        cursor.execute("""
            SELECT id, window_title, process_name, start_time, end_time, duration, synced
            FROM activity_logs
            ORDER BY start_time DESC
            LIMIT 10
        """)
        
        local_entries = cursor.fetchall()
        logger.info(f"Found {len(local_entries)} recent time entries in local database:")
        
        # Display local entries
        for entry in local_entries:
            logger.info(f"ID: {entry[0]}, Title: {entry[1]}, Process: {entry[2]}, Start: {entry[3]}, Synced: {entry[6]}")
        
        # 2. Check Supabase for time entries
        logger.info("Checking Supabase for time entries...")
        try:
            # Get user ID for Supabase query
            user_id = auth_service.user.get("id")
            
            # Get organization ID for Supabase query
            org_id = await sync_service._get_user_org_id(user_id)
            
            if not org_id:
                logger.warning("No organization found for user")
            else:
                logger.info(f"Using organization: {org_id}")
                
                # Query Supabase for activity logs
                result = sync_service.supabase.table("activity_logs").select("*").eq("user_id", user_id).order("start_time", desc=True).limit(10).execute()
                
                if result and result.data:
                    logger.info(f"Found {len(result.data)} time entries in Supabase:")
                    
                    # Display Supabase entries
                    for entry in result.data:
                        logger.info(f"ID: {entry.get('id')}, Title: {entry.get('window_title')}, Process: {entry.get('process_name')}, Start: {entry.get('start_time')}")
                        
                    # Check if local entries match Supabase entries
                    local_ids = [entry[0] for entry in local_entries]
                    supabase_ids = [entry.get('id') for entry in result.data]
                    
                    # Find entries that exist in both places
                    common_ids = set(local_ids).intersection(set(supabase_ids))
                    logger.info(f"Found {len(common_ids)} entries that exist in both local and Supabase")
                    
                    # Find entries only in local database
                    local_only = set(local_ids).difference(set(supabase_ids))
                    if local_only:
                        logger.info(f"Found {len(local_only)} entries only in local database: {local_only}")
                    
                    # Find entries only in Supabase
                    supabase_only = set(supabase_ids).difference(set(local_ids))
                    if supabase_only:
                        logger.info(f"Found {len(supabase_only)} entries only in Supabase: {supabase_only}")
                else:
                    logger.warning("No time entries found in Supabase")
        except Exception as e:
            logger.error(f"Error querying Supabase: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        # 3. Check for unsynchronized time entries
        try:
            if hasattr(db_service, 'get_unsynchronized_time_entries'):
                unsynced_entries = db_service.get_unsynchronized_time_entries(0)
            else:
                unsynced_entries = db_service.get_unsynchronized_activity_logs(0)
            
            if unsynced_entries:
                logger.info(f"Found {len(unsynced_entries)} unsynchronized time entries:")
                for entry in unsynced_entries:
                    logger.info(f"Unsync ID: {entry['id']}, Title: {entry.get('window_title')}, Start: {entry.get('start_time')}")
            else:
                logger.info("No unsynchronized time entries found")
        except Exception as e:
            logger.error(f"Error checking unsynchronized entries: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        
        return True
            
    except Exception as e:
        logger.error(f"Error in find_time_entries: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("=== Finding Time Entries ===")
    asyncio.run(find_time_entries())
