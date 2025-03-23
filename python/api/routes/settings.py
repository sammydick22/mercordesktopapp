"""
Settings API routes for the Time Tracker desktop app.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from api.dependencies import get_current_user

# Setup logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    tags=["settings"],
    responses={404: {"description": "Not found"}},
)

# Temporary placeholder for settings data
# In the real implementation, this will use Supabase and local storage
default_settings = {
    "screenshot_interval": 600,  # 10 minutes
    "screenshot_quality": "medium",
    "auto_sync_interval": 300,  # 5 minutes
    "idle_detection_timeout": 300,  # 5 minutes
    "theme": "system",
    "notifications_enabled": True
}

# Store settings per user
user_settings = {}

# Temporary placeholder for user profiles
# In the real implementation, this will use Supabase
user_profiles = {}

@router.get("/settings")
async def get_settings(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the settings for the current user.
    
    Returns:
        The settings
    """
    user_id = current_user.get("id")
    
    # Get or create settings for this user
    if user_id not in user_settings:
        user_settings[user_id] = default_settings.copy()
    
    return user_settings[user_id]

@router.put("/settings")
async def update_settings(
    settings_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update the settings for the current user.
    
    Args:
        settings_data: The settings data to update
        
    Returns:
        The updated settings
    """
    user_id = current_user.get("id")
    
    # Get or create settings for this user
    if user_id not in user_settings:
        user_settings[user_id] = default_settings.copy()
    
    # Update settings fields
    for key, value in settings_data.items():
        if key in user_settings[user_id]:
            user_settings[user_id][key] = value
    
    logger.info(f"Updated settings for user {user_id}")
    
    return user_settings[user_id]

@router.get("/profile")
async def get_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the profile for the current user.
    
    Returns:
        The profile
    """
    user_id = current_user.get("id")
    
    # Get or create profile for this user
    if user_id not in user_profiles:
        user_profiles[user_id] = {
            "id": user_id,
            "name": current_user.get("email", "").split("@")[0],  # Default to email username
            "email": current_user.get("email", ""),
            "timezone": "UTC",
            "hourly_rate": 0,
            "avatar_url": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    
    return user_profiles[user_id]

@router.put("/profile")
async def update_profile(
    profile_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update the profile for the current user.
    
    Args:
        profile_data: The profile data to update
        
    Returns:
        The updated profile
    """
    user_id = current_user.get("id")
    
    # Get or create profile for this user
    if user_id not in user_profiles:
        user_profiles[user_id] = {
            "id": user_id,
            "name": current_user.get("email", "").split("@")[0],  # Default to email username
            "email": current_user.get("email", ""),
            "timezone": "UTC",
            "hourly_rate": 0,
            "avatar_url": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    
    # Update profile fields
    for key, value in profile_data.items():
        if key in user_profiles[user_id] and key != "id":  # Don't allow ID changes
            user_profiles[user_id][key] = value
    
    # Update the updated_at timestamp
    user_profiles[user_id]["updated_at"] = datetime.utcnow().isoformat()
    
    logger.info(f"Updated profile for user {user_id}")
    
    return user_profiles[user_id]
