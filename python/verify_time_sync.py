"""
Verify time entry synchronization between local SQLite database and Supabase.
This script checks both activity_logs and time_entries tables and compares with Supabase.
"""
import asyncio
import logging
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import uuid
import sqlite3

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Make sure we load environment variables
load_dotenv()

async def verify_time_entries_sync():
    """Check the synchronization state between local and Supabase time entries."""
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
        
        # Create sync service
        logger.info("Creating Supabase sync service...")
        sync_service = SupabaseSyncService(db_service, auth_service)
        logger.info("Sync service created")
        
        # Get connection to database for direct queries
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # 1. Check database schema - table structure
        logger.info("\n=== DATABASE SCHEMA ===")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.info(f"Tables in database: {[t[0] for t in tables]}")
        
        # Check activity_logs table
        cursor.execute("PRAGMA table_info(activity_logs)")
        activity_columns = cursor.fetchall()
        logger.info(f"Activity logs table columns: {[col[1] for col in activity_columns]}")
        
        # Check time_entries table
        cursor.execute("PRAGMA table_info(time_entries)")
        time_entry_columns = cursor.fetchall()
        logger.info(f"Time entries table columns: {[col[1] for col in time_entry_columns]}")
        
        # 2. Check for time entries in both tables
        logger.info("\n=== LOCAL DATABASE CONTENT ===")
        
        # Check time_entries table first (newer approach)
        cursor.execute(
            """
            SELECT id, start_time, end_time, duration, project_id, is_active, synced 
            FROM time_entries 
            ORDER BY start_time DESC LIMIT 10
            """
        )
        time_entries = cursor.fetchall()
        logger.info(f"Found {len(time_entries)} recent time entries in time_entries table")
        
        for entry in time_entries:
            logger.info(f"Time Entry: id={entry[0]}, start={entry[1]}, active={entry[5]}, synced={entry[6]}")
        
        # Check activity_logs table (older approach)
        cursor.execute(
            """
            SELECT id, window_title, start_time, end_time, duration, is_active, synced 
            FROM activity_logs 
            ORDER BY start_time DESC LIMIT 10
            """
        )
        activity_logs = cursor.fetchall()
        logger.info(f"Found {len(activity_logs)} recent activity logs in activity_logs table")
        
        for log in activity_logs:
            logger.info(f"Activity Log: id={log[0]}, title={log[1]}, start={log[2]}, active={log[5]}, synced={log[6]}")
        
        # 3. Check unsynchronized entries in both tables
        cursor.execute("SELECT COUNT(*) FROM time_entries WHERE synced = 0")
        unsynced_entries_count = cursor.fetchone()[0]
        logger.info(f"Found {unsynced_entries_count} unsynchronized time entries in time_entries table")
        
        cursor.execute("SELECT COUNT(*) FROM activity_logs WHERE synced = 0")
        unsynced_logs_count = cursor.fetchone()[0]
        logger.info(f"Found {unsynced_logs_count} unsynchronized activity logs in activity_logs table")
        
        # 4. Check entries in Supabase
        logger.info("\n=== SUPABASE CONTENT ===")
        user_id = auth_service.user.get("id")
        
        try:
            # First check activity_logs table in Supabase
            result = sync_service.supabase.table("activity_logs").select("*").eq("user_id", user_id).order("start_time", desc=True).limit(10).execute()
            
            if result and result.data:
                logger.info(f"Found {len(result.data)} activity logs in Supabase")
                for log in result.data:
                    logger.info(f"Supabase Activity Log: id={log.get('id')}, title={log.get('window_title')}, start={log.get('start_time')}")
            else:
                logger.warning("No activity logs found in Supabase")
        except Exception as e:
            logger.error(f"Error checking Supabase activity logs: {str(e)}")
        
        try:
            # Check if time_entries table exists in Supabase
            logger.info("Checking if time_entries table exists in Supabase...")
            
            # Try to query the time_entries table
            try:
                result = sync_service.supabase.table("time_entries").select("*").eq("user_id", user_id).order("start_time", desc=True).limit(10).execute()
                
                if result and result.data:
                    logger.info(f"Found {len(result.data)} time entries in Supabase time_entries table")
                    for entry in result.data:
                        logger.info(f"Supabase Time Entry: id={entry.get('id')}, project_id={entry.get('project_id')}, start={entry.get('start_time')}")
                else:
                    logger.warning("No time entries found in Supabase time_entries table")
            except Exception as te:
                logger.warning(f"Error querying time_entries table: {str(te)}")
                logger.warning("time_entries table might not exist in Supabase")
        except Exception as e:
            logger.error(f"Error checking Supabase time entries: {str(e)}")
        
        # 5. Connection between table types (if any)
        logger.info("\n=== TABLE RELATIONSHIPS ===")
        
        # Check if any time entries reference activity logs
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND sql LIKE '%activity_log_id%' AND name='time_entries'")
        has_activity_reference = cursor.fetchone()[0] > 0
        logger.info(f"time_entries table references activity_logs: {has_activity_reference}")
        
        # 6. Test sync mechanism for both tables
        logger.info("\n=== SYNC MECHANISM ===")
        
        # Check if database service has the necessary methods for time entries
        has_time_entry_methods = (
            hasattr(db_service, 'get_unsynchronized_time_entries') and 
            hasattr(db_service, 'update_time_entry_sync_status')
        )
        logger.info(f"Database service has time entry sync methods: {has_time_entry_methods}")
        
        # Check if database service has the necessary methods for activity logs
        has_activity_methods = (
            hasattr(db_service, 'get_unsynchronized_activity_logs') and 
            hasattr(db_service, 'update_activity_log_sync_status')
        )
        logger.info(f"Database service has activity log sync methods: {has_activity_methods}")
        
        # Check if sync service has a custom method for time entries sync
        has_custom_time_sync = hasattr(sync_service, 'sync_time_entries')
        logger.info(f"Sync service has custom time entries sync method: {has_custom_time_sync}")
        
        # 7. Core issue: Check how activity logs sync maps to time entries
        # First check if sync service has been extended to handle time entries
        from importlib import util
        has_time_entries_extension = util.find_spec('services.time_entries_extensions') is not None
        logger.info(f"Has dedicated time entries extension module: {has_time_entries_extension}")
        
        # 8. Determine the mismatch cause and solution
        logger.info("\n=== DIAGNOSIS ===")
        
        if unsynced_entries_count > 0 and not has_custom_time_sync:
            logger.info("DIAGNOSIS: time_entries aren't being synchronized because there's no dedicated sync method")
            logger.info("SOLUTION: Implement a sync_time_entries method in SupabaseSyncService or an extension")
        elif not has_time_entry_methods:
            logger.info("DIAGNOSIS: time_entries aren't being synchronized because the database service lacks required methods")
            logger.info("SOLUTION: Add get_unsynchronized_time_entries and update_time_entry_sync_status methods")
        elif len(time_entries) > 0 and unsynced_entries_count > 0:
            logger.info("DIAGNOSIS: time_entries exist and are marked as unsynchronized, but aren't being synced")
            logger.info("SOLUTION: Modify the sync_all method to include time entries synchronization")
            
        # 9. Schema validation - check if Supabase has time_entries
        logger.info("\n=== SUPABASE SCHEMA ===")
        
        try:
            # Get organization ID for RLS policies
            org_id = await sync_service._get_user_org_id(user_id)
            logger.info(f"User's organization ID: {org_id}")
            
            # Use Supabase PostgREST to check if time_entries table exists
            # This won't work directly due to RLS, but error messages will be different
            try:
                result = sync_service.supabase.from_("information_schema").select("table_name").eq("table_schema", "public").execute()
                if result and result.data:
                    logger.info(f"Public schema tables: {[t.get('table_name') for t in result.data]}")
                else:
                    logger.warning("Could not list tables in Supabase public schema (likely due to RLS)")
            except Exception as te:
                logger.warning(f"Error listing Supabase tables: {str(te)}")
        except Exception as e:
            logger.error(f"Error checking Supabase schema: {str(e)}")
        
        # 10. Recommend solution
        logger.info("\n=== RECOMMENDATION ===")
        
        if unsynced_entries_count > 0:
            logger.info("To fix the synchronization issue:")
            logger.info("1. Implement a time_entries synchronization method in supabase_sync_extensions.py")
            logger.info("2. Add it to the extended_sync_all() method to run during full sync")
            logger.info("3. Make sure the Supabase database has a time_entries table with matching schema")
            logger.info("4. If using activity_logs with different structure in Supabase, create a mapping function")
        
        return True
            
    except Exception as e:
        logger.error(f"Error in verification: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    print("=== Time Entry Sync Verification ===")
    asyncio.run(verify_time_entries_sync())
