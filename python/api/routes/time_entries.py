"""
Time entry API routes for the Time Tracker desktop app.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from api.dependencies import get_current_user

# Setup logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/time-entries",
    tags=["time-entries"],
    responses={404: {"description": "Not found"}},
)

# Temporary placeholder for time entry data
# In the real implementation, this will use Supabase through MCP
active_time_entry = None
time_entries = []

@router.post("/start")
async def start_time_entry(
    background_tasks: BackgroundTasks,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    description: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
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
    global active_time_entry
    
    # Check if there's already an active time entry
    if active_time_entry:
        raise HTTPException(status_code=400, detail="There is already an active time entry")
    
    # Create new time entry
    time_entry = {
        "id": f"te_{len(time_entries) + 1}",
        "start_time": datetime.utcnow().isoformat(),
        "end_time": None,
        "duration": 0,
        "project_id": project_id,
        "task_id": task_id,
        "description": description,
        "is_active": True,
        "synced": False
    }
    
    # Store the time entry
    active_time_entry = time_entry
    time_entries.append(time_entry)
    
    # Add background task to start screenshot capturing
    # This would be implemented with the screenshot service
    # background_tasks.add_task(start_screenshot_capturing, time_entry["id"])
    
    logger.info(f"Started time entry {time_entry['id']}")
    
    return time_entry

@router.post("/stop")
async def stop_time_entry(
    description: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Stop the active time entry.
    
    Args:
        description: Optional description to add to the time entry
        
    Returns:
        The stopped time entry
    """
    global active_time_entry
    
    # Check if there's an active time entry
    if not active_time_entry:
        raise HTTPException(status_code=404, detail="No active time entry found")
    
    # Update the time entry
    end_time = datetime.utcnow()
    start_time = datetime.fromisoformat(active_time_entry["start_time"].replace("Z", "+00:00"))
    duration = int((end_time - start_time).total_seconds())
    
    active_time_entry["end_time"] = end_time.isoformat()
    active_time_entry["duration"] = duration
    active_time_entry["is_active"] = False
    
    # Add description if provided
    if description:
        active_time_entry["description"] = description
    
    # Queue for synchronization
    # This would use the synchronization service in a real implementation
    
    logger.info(f"Stopped time entry {active_time_entry['id']}")
    
    # Get the stopped time entry
    stopped_entry = active_time_entry
    
    # Clear the active time entry
    active_time_entry = None
    
    return stopped_entry

@router.get("/current")
async def get_current_time_entry(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the current active time entry.
    
    Returns:
        The active time entry or None
    """
    if not active_time_entry:
        return {"active": False}
    
    return {
        "active": True,
        "time_entry": active_time_entry
    }

@router.get("/")
async def list_time_entries(
    limit: int = 10,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List time entries with pagination.
    
    Args:
        limit: Maximum number of entries to return
        offset: Number of entries to skip
        
    Returns:
        List of time entries
    """
    start = offset
    end = offset + limit
    
    return {
        "total": len(time_entries),
        "time_entries": time_entries[start:end]
    }
