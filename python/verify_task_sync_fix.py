"""
Verification script to confirm that task synchronization is working correctly.
This script specifically tests that project tasks are properly synchronized with Supabase.
"""
import asyncio
import logging
import os
import sys
from dotenv import load_dotenv
import uuid
from datetime import datetime

# Ensure proper module resolution
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Import necessary modules
from services.database import DatabaseService
from services.supabase_auth import SupabaseAuthService
from services.supabase_sync import SupabaseSyncService

# Apply database extensions manually
from utils.patch_loader import apply_patches_to_class

async def verify_task_sync():
    """Verify that task synchronization is working correctly."""
    
    logger.info("Starting task sync verification")
    
    # Apply database extensions
    logger.info("Applying database extensions")
    db_extension_count = apply_patches_to_class(DatabaseService, "database_extensions_patch")
    logger.info(f"Applied {db_extension_count} database extensions")
    
    # Initialize services
    logger.info("Initializing services")
    db_service = DatabaseService()
    auth_service = SupabaseAuthService()
    sync_service = SupabaseSyncService(db_service, auth_service)
    
    # Ensure we're authenticated before proceeding
    await ensure_authentication(auth_service)
    
    # Check for existing tasks
    logger.info("Checking for unsynchronized project tasks...")
    
    try:
        project_tasks = db_service.get_unsynchronized_project_tasks()
        
        if project_tasks:
            logger.info(f"Found {len(project_tasks)} unsynchronized project tasks")
            for task in project_tasks:
                logger.info(f"  - Task {task['id']}: {task['name']} (Project: {task['project_id']})")
        else:
            logger.info("No unsynchronized project tasks found")
            
            # Create a test task if none exist
            logger.info("Creating a test project task for verification")
            project_id = await get_or_create_test_project(db_service, auth_service)
            
            task_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            conn = db_service._get_connection()
            cursor = conn.cursor()
            
            cursor.execute(
                '''
                INSERT INTO project_tasks 
                (id, name, description, project_id, estimated_hours, 
                is_active, synced, created_at, updated_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    task_id,
                    "Test Task for Sync Verification",
                    "This is a test task to verify task sync functionality",
                    project_id,
                    2.5,  # estimated hours
                    1,    # is_active = True
                    0,    # Not synced
                    now,
                    now
                )
            )
            
            conn.commit()
            logger.info(f"Created test task with ID: {task_id}")
            
            # Check again
            project_tasks = db_service.get_unsynchronized_project_tasks()
            logger.info(f"Now have {len(project_tasks)} unsynchronized project tasks")
        
        # Initialize the sync service
        logger.info("Initializing sync service...")
        await sync_service.initialize()
        
        # Sync tasks
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
        
    except Exception as e:
        logger.error(f"Error during task sync verification: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("Verification completed")

async def ensure_authentication(auth_service):
    """Ensure we have a valid authentication session."""
    
    # Check if already authenticated
    if auth_service.is_authenticated():
        logger.info("Already authenticated")
        user = await auth_service.get_user()
        logger.info(f"Authenticated as: {user.get('email', 'Unknown email')}")
        return True
    
    # Try to authenticate with environment variables first
    email = os.getenv("SUPABASE_TEST_EMAIL")
    password = os.getenv("SUPABASE_TEST_PASSWORD")
    
    if email and password:
        try:
            logger.info(f"Attempting login with environment variables: {email}")
            await auth_service.login(email, password)
            
            if auth_service.is_authenticated():
                user = await auth_service.get_user()
                logger.info(f"Successfully authenticated as: {user.get('email', 'Unknown email')}")
                return True
            else:
                logger.warning("Environment variable login failed")
        except Exception as e:
            logger.warning(f"Environment variable login error: {str(e)}")
    else:
        logger.info("No test credentials found in environment variables")
    
    # If environment variables failed, prompt for credentials
    try:
        # Simple input prompt for credentials
        print("\n=== Authentication Required for Task Sync Test ===")
        email = input("Enter Supabase email: ").strip()
        import getpass
        password = getpass.getpass("Enter password: ").strip()
        
        if not email or not password:
            raise Exception("Email and password are required")
        
        logger.info(f"Attempting login with provided credentials: {email}")
        await auth_service.login(email, password)
        
        if auth_service.is_authenticated():
            user = await auth_service.get_user()
            logger.info(f"Successfully authenticated as: {user.get('email', 'Unknown email')}")
            return True
        else:
            logger.error("Login failed with provided credentials")
            raise Exception("Authentication failed")
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise Exception("Unable to authenticate")

async def get_or_create_test_project(db_service, auth_service):
    """Get or create a test project for task sync verification."""
    
    # Authentication is already handled by ensure_authentication()
    
    # Get user ID
    user = await auth_service.get_user()
    user_id = user["id"]
    
    # Check if we already have a test project
    conn = db_service._get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        '''
        SELECT id FROM projects 
        WHERE name LIKE 'Test Project for Sync%' AND user_id = ? 
        LIMIT 1
        ''',
        (user_id,)
    )
    
    result = cursor.fetchone()
    
    if result:
        return result[0]  # Return existing project ID
    
    # Create a new test project
    project_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    cursor.execute(
        '''
        INSERT INTO projects 
        (id, name, description, color, hourly_rate, 
        is_billable, is_active, user_id, synced, created_at, updated_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''',
        (
            project_id,
            "Test Project for Sync Verification",
            "This is a test project to verify task sync functionality",
            "#4CAF50",
            50.0,
            1,  # is_billable = True
            1,  # is_active = True
            user_id,
            0,  # Not synced
            now,
            now
        )
    )
    
    conn.commit()
    logger.info(f"Created test project with ID: {project_id}")
    
    return project_id

if __name__ == "__main__":
    asyncio.run(verify_task_sync())
