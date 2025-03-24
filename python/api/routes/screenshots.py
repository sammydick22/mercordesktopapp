"""
Screenshot API routes for the Time Tracker desktop app.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import logging
import uuid

from api.dependencies import get_current_user
from core.screenshot_service import ScreenshotService
from services.database import DatabaseService

# Setup logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/screenshots",
    tags=["screenshots"],
    responses={404: {"description": "Not found"}},
)

# Create database service
db_service = DatabaseService()

# Helper to get screenshot directory
def get_screenshots_dir():
    screenshots_dir = os.path.join(os.path.expanduser("~"), "TimeTracker", "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)
    return screenshots_dir

# Initialize screenshot service
screenshot_service = ScreenshotService()

# Initialize database tables if needed
def initialize_db():
    try:
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Create screenshots table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS screenshots (
            id TEXT PRIMARY KEY,
            filepath TEXT NOT NULL,
            thumbnail_path TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            time_entry_id TEXT,
            activity_log_id INTEGER,
            synced BOOLEAN NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Check if activity_log_id column exists
        cursor.execute("PRAGMA table_info(screenshots)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add time_entry_id if it doesn't exist (for backward compatibility)
        if "time_entry_id" not in columns:
            cursor.execute("ALTER TABLE screenshots ADD COLUMN time_entry_id TEXT")
            logger.info("Added time_entry_id column to screenshots table")
            
        # Add activity_log_id if it doesn't exist (for backward compatibility)
        if "activity_log_id" not in columns:
            cursor.execute("ALTER TABLE screenshots ADD COLUMN activity_log_id INTEGER")
            logger.info("Added activity_log_id column to screenshots table")
        
        conn.commit()
        logger.info("Screenshots database initialized")
    except Exception as e:
        logger.error(f"Error initializing screenshots database: {str(e)}")

# Initialize database on startup
initialize_db()

@router.post("/capture")
async def capture_screenshot(
    background_tasks: BackgroundTasks,
    time_entry_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Capture a screenshot.
    
    Args:
        time_entry_id: Optional time entry ID to associate with the screenshot
        
    Returns:
        The screenshot metadata
    """
    # Use the screenshot service to capture a real screenshot
    screenshot_data = screenshot_service.capture_screenshot(time_entry_id)
    
    if not screenshot_data:
        raise HTTPException(status_code=500, detail="Failed to capture screenshot")
    
    try:
        # Generate a UUID for the screenshot
        screenshot_id = str(uuid.uuid4())
        
        # Get current timestamp
        timestamp = datetime.now().isoformat()
        
        # Prepare query and parameters
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Try to get the active activity log if available
        activity_log_id = None
        try:
            active_activity = db_service.get_active_activity()
            if active_activity:
                activity_log_id = active_activity.get('id')
                logger.debug(f"Found active activity log: {activity_log_id}")
        except Exception as e:
            logger.warning(f"Error getting active activity: {str(e)}")
        
        cursor.execute(
            '''
            INSERT INTO screenshots 
            (id, filepath, thumbnail_path, timestamp, time_entry_id, activity_log_id, synced, created_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                screenshot_id,
                screenshot_data['filepath'],
                screenshot_data['thumbnail_path'],
                timestamp,
                time_entry_id,
                activity_log_id,
                0,  # Not synced
                timestamp
            )
        )
        
        conn.commit()
        
        # Create response screenshot object
        screenshot = {
            "id": screenshot_id,
            "filepath": screenshot_data['filepath'],
            "thumbnail_path": screenshot_data['thumbnail_path'],
            "timestamp": timestamp,
            "time_entry_id": time_entry_id,
            "synced": False,
            "created_at": timestamp
        }
        
        logger.info(f"Captured screenshot {screenshot_id}")
        
        return screenshot
    
    except Exception as e:
        logger.error(f"Error saving screenshot to database: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save screenshot: {str(e)}")

@router.get("/")
async def list_screenshots(
    limit: int = 10,
    offset: int = 0,
    time_entry_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List screenshots with pagination and optional filtering.
    
    Args:
        limit: Maximum number of screenshots to return
        offset: Number of screenshots to skip
        time_entry_id: Optional time entry ID to filter by
        
    Returns:
        List of screenshots
    """
    try:
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Build query
        query = '''
        SELECT 
            id, filepath, thumbnail_path, timestamp, time_entry_id, activity_log_id,
            synced, created_at
        FROM screenshots 
        WHERE 1=1
        '''
        
        params = []
        
        # Add filters if provided
        if time_entry_id:
            query += ' AND time_entry_id = ?'
            params.append(time_entry_id)
        
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query})"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
            
        # Add sorting and pagination
        query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        # Execute query
        cursor.execute(query, params)
        
        # Get results
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        column_names = [
            'id', 'filepath', 'thumbnail_path', 'timestamp', 'time_entry_id', 'activity_log_id',
            'synced', 'created_at'
        ]
        
        screenshots_list = [
            {
                column_names[i]: row[i] if row[i] is not None else None 
                for i in range(len(column_names))
            }
            for row in results
        ]

        # Convert synced to boolean
        for s in screenshots_list:
            s['synced'] = bool(s['synced'])
        
        return {
            "total": total,
            "screenshots": screenshots_list
        }
    except Exception as e:
        logger.error(f"Error getting screenshots: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get screenshots: {str(e)}")

@router.get("/{screenshot_id}")
async def get_screenshot(
    screenshot_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a specific screenshot by ID.
    
    Args:
        screenshot_id: The screenshot ID
        
    Returns:
        The screenshot metadata
    """
    try:
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Get the screenshot
        cursor.execute(
            '''
            SELECT 
                id, filepath, thumbnail_path, timestamp, time_entry_id,
                activity_log_id, synced, created_at
            FROM screenshots 
            WHERE id = ?
            ''',
            (screenshot_id,)
        )
        
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Screenshot not found")
            
        # Convert to dictionary
        column_names = [
            'id', 'filepath', 'thumbnail_path', 'timestamp', 'time_entry_id',
            'activity_log_id', 'synced', 'created_at'
        ]
        
        screenshot = {
            column_names[i]: row[i] if row[i] is not None else None 
            for i in range(len(column_names))
        }
        
        # Convert synced to boolean
        screenshot['synced'] = bool(screenshot['synced'])
        
        return screenshot
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting screenshot: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get screenshot: {str(e)}")

@router.get("/{screenshot_id}/image")
async def get_screenshot_image(
    screenshot_id: str
):
    """
    Get the image file for a specific screenshot.
    
    Args:
        screenshot_id: The screenshot ID
        
    Returns:
        The screenshot image file
    """
    try:
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Get the screenshot filepath
        cursor.execute(
            'SELECT filepath FROM screenshots WHERE id = ?',
            (screenshot_id,)
        )
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Screenshot not found")
            
        filepath = result[0]
        
        # Check if file exists
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail="Screenshot file not found")
            
        # Return the file
        return FileResponse(filepath)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting screenshot image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get screenshot image: {str(e)}")

@router.get("/{screenshot_id}/thumbnail")
async def get_screenshot_thumbnail(
    screenshot_id: str
):
    """
    Get the thumbnail image for a specific screenshot.
    
    Args:
        screenshot_id: The screenshot ID
        
    Returns:
        The screenshot thumbnail image file
    """
    try:
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Get the screenshot thumbnail path
        cursor.execute(
            'SELECT thumbnail_path FROM screenshots WHERE id = ?',
            (screenshot_id,)
        )
        
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Screenshot not found")
            
        thumbnail_path = result[0]
        
        # Check if file exists
        if not os.path.exists(thumbnail_path):
            raise HTTPException(status_code=404, detail="Screenshot thumbnail file not found")
            
        # Return the file
        return FileResponse(thumbnail_path)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting screenshot thumbnail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get screenshot thumbnail: {str(e)}")
