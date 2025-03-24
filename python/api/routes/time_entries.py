"""
Time entry API routes for the Time Tracker desktop app.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import uuid

from api.dependencies import get_current_user
from services.database import DatabaseService

# Setup logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/time-entries",
    tags=["time-entries"],
    responses={404: {"description": "Not found"}},
)

# Use dependency injection for database service
from api.dependencies import get_db_service

@router.post("/start")
async def start_time_entry(
    background_tasks: BackgroundTasks,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    description: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """
    Start a new time entry.
    
    Args:
        project_id: Optional project ID
        task_id: Optional task ID
        description: Optional description
        
    Returns:
        The created time entry
    """
    # Get user ID
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found")
    
    # Check if there's already an active time entry
    active_entry = db_service.get_active_time_entry(user_id)
    if active_entry:
        raise HTTPException(status_code=400, detail="There is already an active time entry")
    
    # Create new time entry in database
    time_entry = db_service.create_time_entry(
        user_id=user_id,
        project_id=project_id,
        task_id=task_id,
        description=description
    )
    
    if not time_entry:
        raise HTTPException(status_code=500, detail="Failed to create time entry")
    
    # Add background task to start screenshot capturing
    # This would be implemented with the screenshot service
    # background_tasks.add_task(start_screenshot_capturing, time_entry["id"])
    
    logger.info(f"Started time entry {time_entry['id']} for user {user_id}")
    
    return {"time_entry": time_entry}

@router.post("/stop")
async def stop_time_entry(
    description: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """
    Stop the active time entry.
    
    Args:
        description: Optional description to add to the time entry
        
    Returns:
        The stopped time entry
    """
    # Get user ID
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found")
    
    # Get the active time entry for this user
    active_entry = db_service.get_active_time_entry(user_id)
    if not active_entry:
        raise HTTPException(status_code=404, detail="No active time entry found")
    
    # End the time entry
    updated_entry = db_service.end_time_entry(active_entry["id"], description)
    if not updated_entry:
        raise HTTPException(status_code=500, detail="Failed to stop time entry")
    
    logger.info(f"Stopped time entry {updated_entry['id']} for user {user_id}")
    
    return {"time_entry": updated_entry}

@router.get("/current")
async def get_current_time_entry(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """
    Get the current active time entry.
    
    Returns:
        The active time entry or None
    """
    # Get user ID
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found")
    
    # Get the active time entry for this user
    active_entry = db_service.get_active_time_entry(user_id)
    
    if not active_entry:
        return {"active": False}
    
    return {
        "active": True,
        "time_entry": active_entry
    }

@router.get("/")
async def list_time_entries(
    limit: int = 10,
    offset: int = 0,
    project_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_service: DatabaseService = Depends(get_db_service)
):
    """
    List time entries with pagination.
    
    Args:
        limit: Maximum number of entries to return
        offset: Number of entries to skip
        project_id: Filter by project ID (optional)
        start_date: Filter by start date (optional)
        end_date: Filter by end date (optional)
        
    Returns:
        List of time entries
    """
    # Get user ID
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found")
    
    # Get time entries for this user
    result = db_service.get_time_entries(
        user_id=user_id,
        limit=limit,
        offset=offset,
        project_id=project_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return result
