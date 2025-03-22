"""
Screenshot API routes for the Time Tracker desktop app.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import FileResponse
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import logging

from api.dependencies import get_current_user

# Setup logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/screenshots",
    tags=["screenshots"],
    responses={404: {"description": "Not found"}},
)

# Placeholder for screenshot data
# In the real implementation, this would use an actual database
screenshots = []

# Helper to get screenshot directory
def get_screenshots_dir():
    screenshots_dir = os.path.join(os.path.expanduser("~"), "TimeTracker", "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)
    return screenshots_dir

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
    # This would use the screenshot service in a real implementation
    # For now, we'll just create a mock screenshot entry
    
    screenshot_id = f"ss_{len(screenshots) + 1}"
    timestamp = datetime.utcnow()
    filename = f"screenshot_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
    thumbnail_filename = f"screenshot_{timestamp.strftime('%Y%m%d_%H%M%S')}_thumb.png"
    
    filepath = os.path.join(get_screenshots_dir(), filename)
    thumbnail_path = os.path.join(get_screenshots_dir(), thumbnail_filename)
    
    # Mock screenshot capturing
    # In a real implementation, this would use the mss library to capture the screen
    # and Pillow to create a thumbnail
    
    # Create mock files (empty)
    with open(filepath, 'w') as f:
        f.write("Mock screenshot")
    
    with open(thumbnail_path, 'w') as f:
        f.write("Mock thumbnail")
    
    # Create screenshot entry
    screenshot = {
        "id": screenshot_id,
        "timestamp": timestamp.isoformat(),
        "filepath": filepath,
        "thumbnail_path": thumbnail_path,
        "time_entry_id": time_entry_id,
        "synced": False
    }
    
    # Store screenshot metadata
    screenshots.append(screenshot)
    
    logger.info(f"Captured screenshot {screenshot_id}")
    
    return screenshot

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
    # Filter by time entry if specified
    filtered_screenshots = screenshots
    if time_entry_id:
        filtered_screenshots = [s for s in screenshots if s["time_entry_id"] == time_entry_id]
    
    # Apply pagination
    start = offset
    end = offset + limit
    
    return {
        "total": len(filtered_screenshots),
        "screenshots": filtered_screenshots[start:end]
    }

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
    # Find the screenshot
    for screenshot in screenshots:
        if screenshot["id"] == screenshot_id:
            return screenshot
    
    # Not found
    raise HTTPException(status_code=404, detail="Screenshot not found")

@router.get("/{screenshot_id}/image")
async def get_screenshot_image(
    screenshot_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the image file for a specific screenshot.
    
    Args:
        screenshot_id: The screenshot ID
        
    Returns:
        The screenshot image file
    """
    # Find the screenshot
    for screenshot in screenshots:
        if screenshot["id"] == screenshot_id:
            # Return the file
            return FileResponse(screenshot["filepath"])
    
    # Not found
    raise HTTPException(status_code=404, detail="Screenshot not found")

@router.get("/{screenshot_id}/thumbnail")
async def get_screenshot_thumbnail(
    screenshot_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the thumbnail image for a specific screenshot.
    
    Args:
        screenshot_id: The screenshot ID
        
    Returns:
        The screenshot thumbnail image file
    """
    # Find the screenshot
    for screenshot in screenshots:
        if screenshot["id"] == screenshot_id:
            # Return the file
            return FileResponse(screenshot["thumbnail_path"])
    
    # Not found
    raise HTTPException(status_code=404, detail="Screenshot not found")
