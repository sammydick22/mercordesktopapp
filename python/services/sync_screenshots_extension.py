"""
Extension module for adding screenshot sync functionality to SupabaseSyncService.
"""
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

# Setup logger
logger = logging.getLogger(__name__)

def get_current_org_id(self) -> Optional[str]:
    """
    Get the current user's organization ID.
    
    Returns:
        str: Organization ID or None if not found
    """
    try:
        user_id = self.auth_service.user.get("id")
        if not user_id:
            return None
            
        # Check local database first for organization membership
        org_membership = self.db_service.get_user_org_membership(user_id)
        if org_membership and org_membership.get("org_id"):
            return org_membership["org_id"]
            
        return None
    except Exception as e:
        logger.error(f"Error getting current organization ID: {str(e)}")
        return None

async def sync_screenshots(self) -> Dict[str, Any]:
    """
    Synchronize screenshots from local database to Supabase.
    
    Returns:
        dict: Sync results with counts and status
    """
    if not self.supabase:
        logger.error("Supabase client not initialized")
        return {"synced": 0, "failed": 0, "status": "error"}
        
    if not self.auth_service.is_authenticated():
        logger.warning("Cannot sync screenshots: Not authenticated")
        return {"synced": 0, "failed": 0, "status": "not_authenticated"}
        
    try:
        # Only set is_syncing flag when called directly (not from sync_all)
        if not self.is_syncing:
            self.is_syncing = True
        self.sync_failed = False
        self.sync_error = None
        
        # Get user and organization data
        user_id = self.auth_service.user.get("id")
        
        # Get unsynchronized screenshots
        # Pass None to get all unsynchronized screenshots (synced=0)
        # No last_id filter is needed since we're using the modified query
        screenshots = self.db_service.get_unsynchronized_screenshots(None)
        
        if not screenshots:
            logger.info("No screenshots to sync")
            self.is_syncing = False
            return {"synced": 0, "failed": 0, "status": "no_data"}
        
        logger.info(f"Syncing {len(screenshots)} screenshots")
        
        # Prepare screenshots for Supabase
        supabase_screenshots = []
        for screenshot in screenshots:
            # Create a clean record with ONLY the fields that exist in Supabase schema
            # We're completely recreating the object to avoid any field name leakage
            clean_record = {}
            
            # Required fields
            clean_record["id"] = screenshot["id"]
            clean_record["user_id"] = user_id
            clean_record["org_id"] = self.get_current_org_id()
            clean_record["image_url"] = screenshot.get("filepath", "")
            clean_record["taken_at"] = screenshot.get("timestamp") or screenshot.get("created_at")
            clean_record["created_at"] = datetime.now().isoformat()
            
            # Optional fields
            if screenshot.get("thumbnail_path"):
                clean_record["thumbnail_url"] = screenshot.get("thumbnail_path")
            if screenshot.get("activity_log_id"):
                clean_record["activity_log_id"] = screenshot.get("activity_log_id")
            if screenshot.get("created_at"):
                clean_record["client_created_at"] = screenshot.get("created_at")
            
            # Log the record being sent
            logger.debug(f"Sending screenshot record to Supabase: {clean_record}")
            
            supabase_screenshots.append(clean_record)
        
        # Split into batches to avoid request size limits
        batch_size = 20
        batches = [supabase_screenshots[i:i + batch_size] for i in range(0, len(supabase_screenshots), batch_size)]
        
        synced_count = 0
        failed_count = 0
        
        for batch_index, batch in enumerate(batches):
            try:
                logger.info(f"Processing screenshots batch {batch_index+1}/{len(batches)} ({len(batch)} items)")
                
                # Use Supabase client to insert data
                # Be explicit about the columns we're using to match the schema exactly
                result = self.supabase.table("screenshots").upsert(
                    batch,
                    returning="id,user_id,org_id,image_url,thumbnail_url,taken_at,activity_log_id,client_created_at,created_at"
                ).execute()
                
                if result and result.data:
                    batch_synced_count = len(result.data)
                    synced_count += batch_synced_count
                    logger.info(f"Successfully synced {batch_synced_count} screenshots to Supabase")
                    
                    # Update local database with sync status
                    for item in result.data:
                        try:
                            # Get the ID from the result
                            screenshot_id = item.get("id")
                            if screenshot_id:
                                logger.debug(f"Updating sync status for screenshot: {screenshot_id}")
                                self.db_service.update_screenshot_sync_status(screenshot_id, True)
                            else:
                                logger.warning(f"Could not find ID in screenshot response: {item}")
                        except Exception as update_error:
                            logger.error(f"Error updating screenshot sync status: {str(update_error)}")
                else:
                    failed_count += len(batch)
                    logger.error(f"Sync error: No response data for batch {batch_index+1}")
                    
            except Exception as e:
                failed_count += len(batch)
                logger.error(f"Batch sync error for batch {batch_index+1}: {str(e)}")
        
        logger.info(f"Screenshots sync complete: {synced_count} synced, {failed_count} failed")
        
        return {
            "synced": synced_count,
            "failed": failed_count,
            "status": "complete" if failed_count == 0 else "partial"
        }
            
    except Exception as e:
        logger.error(f"Screenshots sync error: {str(e)}")
        import traceback
        logger.error(f"Screenshots sync traceback: {traceback.format_exc()}")
        self.sync_failed = True
        self.sync_error = str(e)
        return {"synced": 0, "failed": len(screenshots) if 'screenshots' in locals() else 0, "status": "error"}
        
    finally:
        self.is_syncing = False
