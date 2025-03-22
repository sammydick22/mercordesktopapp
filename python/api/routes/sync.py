"""
Synchronization routes for the Time Tracker API.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import Dict, Any

from services.supabase_auth import SupabaseAuthService
from services.supabase_sync import SupabaseSyncService
from api.dependencies import get_auth_service, get_sync_service, get_current_user

router = APIRouter(prefix="/sync", tags=["synchronization"])

@router.post("/all")
async def sync_all(sync_service: SupabaseSyncService = Depends(get_sync_service),
                  user: Dict[str, Any] = Depends(get_current_user)):
    """
    Synchronize all data with Supabase.
    
    This syncs activity logs, screenshots, and organization data.
    Requires authentication.
    """
    try:
        result = await sync_service.sync_all()
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                           detail=f"Sync error: {str(e)}")

@router.post("/activities")
async def sync_activities(sync_service: SupabaseSyncService = Depends(get_sync_service),
                         user: Dict[str, Any] = Depends(get_current_user)):
    """
    Synchronize only activity logs with Supabase.
    
    Requires authentication.
    """
    try:
        result = await sync_service.sync_activity_logs()
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                           detail=f"Activity sync error: {str(e)}")

@router.post("/screenshots")
async def sync_screenshots(sync_service: SupabaseSyncService = Depends(get_sync_service),
                          user: Dict[str, Any] = Depends(get_current_user)):
    """
    Synchronize only screenshots with Supabase.
    
    Requires authentication.
    """
    try:
        result = await sync_service.sync_screenshots()
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                           detail=f"Screenshot sync error: {str(e)}")

@router.post("/organization")
async def sync_organization(sync_service: SupabaseSyncService = Depends(get_sync_service),
                           user: Dict[str, Any] = Depends(get_current_user)):
    """
    Synchronize organization data from Supabase.
    
    Requires authentication.
    """
    try:
        result = await sync_service.sync_organization_data()
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                           detail=f"Organization sync error: {str(e)}")

@router.get("/status")
async def get_sync_status(sync_service: SupabaseSyncService = Depends(get_sync_service)):
    """
    Get the current synchronization status.
    
    This endpoint doesn't require authentication to allow checking
    sync status before login.
    """
    try:
        # First initialize the sync service
        initialized = await sync_service.initialize()
        
        return {
            "initialized": initialized,
            "is_syncing": sync_service.is_syncing,
            "sync_error": sync_service.sync_error if hasattr(sync_service, "sync_error") else None,
            "last_sync": sync_service.last_sync if hasattr(sync_service, "last_sync") else {}
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                           detail=f"Error getting sync status: {str(e)}")

@router.post("/background")
async def start_background_sync(background_tasks: BackgroundTasks,
                               sync_service: SupabaseSyncService = Depends(get_sync_service),
                               user: Dict[str, Any] = Depends(get_current_user)):
    """
    Start a background synchronization task.
    
    This allows the sync to happen asynchronously without blocking the API response.
    Requires authentication.
    """
    if sync_service.is_syncing:
        return {"message": "Sync already in progress"}
    
    # Start sync in background task
    background_tasks.add_task(sync_service.sync_all)
    return {"message": "Background sync started"}
