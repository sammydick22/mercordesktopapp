"""
Test script to verify that task synchronization is working correctly after our fix.
"""
import asyncio
import logging
from services.database import DatabaseService
from services.supabase_auth import SupabaseAuthService
from services.supabase_sync import SupabaseSyncService
import os
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def test_task_sync():
    """Test the task synchronization feature with the updated code."""
    
    # Initialize services
    db_service = DatabaseService()
    auth_service = SupabaseAuthService()
    sync_service = SupabaseSyncService(db_service, auth_service)
    
    # Check for existing tasks that need to be synced
    logger.info("Checking for unsynchronized project tasks...")
    project_tasks = db_service.get_unsynchronized_project_tasks()
    
    if project_tasks:
        logger.info(f"Found {len(project_tasks)} unsynchronized project tasks")
        for task in project_tasks:
            logger.info(f"  - Task {task['id']}: {task['name']} (Project: {task['project_id']})")
    else:
        logger.info("No unsynchronized project tasks found")
    
    # Initialize the sync service
    logger.info("Initializing sync service...")
    await sync_service.initialize()
    
    # Only run if we have unsynchronized tasks
    if project_tasks:
        # Now try to sync tasks specifically
        logger.info("Starting project tasks sync...")
        result = await sync_service.sync_tasks()
        
        # Log the result
        logger.info(f"Sync result: {result}")
        
        if result['status'] == 'complete':
            logger.info("Task synchronization was successful!")
            
            # Check if tasks were marked as synced
            tasks_after = db_service.get_unsynchronized_project_tasks()
            if not tasks_after:
                logger.info("All tasks were marked as synchronized!")
            else:
                logger.info(f"Still have {len(tasks_after)} unsynchronized tasks")
        else:
            logger.error(f"Task synchronization failed or was incomplete: {result}")
    
    logger.info("Test completed")

if __name__ == "__main__":
    asyncio.run(test_task_sync())
