"""
Supabase synchronization service for the desktop application.
"""
import logging
import os
import json
import asyncio
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime

# Local imports
from .database import DatabaseService
from .supabase_auth import SupabaseAuthService
from .load_sync_screenshot_extension import load_screenshot_extension

# Setup logger
logger = logging.getLogger(__name__)

class SupabaseSyncService:
    """
    Service for synchronizing local data with Supabase.
    
    This service manages the bidirectional synchronization:
    - Activity logs from local database to Supabase
    - Screenshots from local storage to Supabase Storage
    - Organization and user data from Supabase to local database
    """
    
    def __init__(
        self, 
        db_service: DatabaseService, 
        auth_service: SupabaseAuthService,
        supabase_url: str = None,
        supabase_key: str = None
    ):
        """
        Initialize the Supabase sync service.
        
        Args:
            db_service: Database service for local data
            auth_service: Authentication service for Supabase
            supabase_url: The Supabase project URL
            supabase_key: The Supabase anon key
        """
        self.db_service = db_service
        self.auth_service = auth_service
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_ANON_KEY")
        
        # Get Supabase client from auth service
        self.supabase = self.auth_service.supabase if self.auth_service else None
        
        if not self.supabase:
            logger.warning("Supabase client not available from auth service")
        
        # Sync state
        self.last_sync = {}
        self.is_syncing = False
        self.sync_failed = False
        self.sync_error = None
        
        # Storage bucket name
        self.screenshots_bucket = "screenshots"
        
        # Load last sync state
        self._load_sync_state()
        
    async def initialize(self) -> bool:
        """
        Initialize the sync service.
        
        Returns:
            bool: True if initialization was successful
        """
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return False
            
        try:
            # Skip bucket check/creation during testing
            logger.info(f"Assuming screenshots bucket '{self.screenshots_bucket}' exists")
            
            # Note: This section is commented out due to permission issues
            # In a production environment, you should create this bucket manually
            # or modify this code to use appropriate service role credentials
            
            # try:
            #     # Check if bucket exists
            #     self.supabase.storage.get_bucket(self.screenshots_bucket)
            #     logger.info(f"Screenshots bucket '{self.screenshots_bucket}' exists")
            # except Exception:
            #     # Create bucket if it doesn't exist
            #     logger.info(f"Creating screenshots bucket '{self.screenshots_bucket}'")
            #     self.supabase.storage.create_bucket(
            #         id=self.screenshots_bucket,
            #         options={"public": True}
            #     )
                
            # Load organization info if user is authenticated
            if self.auth_service.is_authenticated():
                await self.sync_organization_data()
                
            return True
            
        except Exception as e:
            logger.error(f"Sync initialization error: {str(e)}")
            return False
            
    async def sync_activity_logs(self) -> Dict[str, Any]:
        """
        Synchronize activity logs (time entries) from local database to Supabase.
        
        Uses improved error handling and schema validation similar to user profiles and settings.
        
        Returns:
            dict: Sync results with counts and status
        """
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return {"synced": 0, "failed": 0, "status": "error"}
            
        if not self.auth_service.is_authenticated():
            logger.warning("Cannot sync activity logs: Not authenticated")
            return {"synced": 0, "failed": 0, "status": "not_authenticated"}
            
        try:
            # Only set is_syncing flag when called directly (not from sync_all)
            if not self.is_syncing:
                self.is_syncing = True
            self.sync_failed = False
            self.sync_error = None
            
            # Get user and organization data
            user_id = self.auth_service.user.get("id")
            org_id = await self._get_user_org_id(user_id)
            
            if not org_id:
                logger.warning("Cannot sync activity logs: No organization found")
                self.is_syncing = False
                return {"synced": 0, "failed": 0, "status": "no_organization"}
            
            # Get last activity log sync ID
            last_sync_id = self.last_sync.get("activity_logs", {}).get("last_id", 0)
            
            # Get unsynchronized activity logs
            try:
                # First try the correct method for activity logs
                activity_logs = self.db_service.get_unsynchronized_activity_logs(last_sync_id)
            except AttributeError:
                try:
                    # Fallback to time entries method as a last resort
                    logger.warning("get_unsynchronized_activity_logs method not found, falling back to get_unsynchronized_time_entries")
                    activity_logs = self.db_service.get_unsynchronized_time_entries(last_sync_id)
                except AttributeError:
                    logger.error("Neither get_unsynchronized_activity_logs nor get_unsynchronized_time_entries methods found")
                    self.is_syncing = False
                    return {"synced": 0, "failed": 0, "status": "error"}
            
            if not activity_logs:
                logger.info("No activity logs to sync")
                self.is_syncing = False
                return {"synced": 0, "failed": 0, "status": "no_data"}
            
            logger.info(f"Syncing {len(activity_logs)} activity logs")
            
            # Prepare activity logs for Supabase with proper field validation and type conversion
            # The key issue: activity_logs use numeric auto-increment IDs locally,
            # but Supabase expects UUIDs. We'll let Supabase generate the UUIDs.
            import uuid
            
            supabase_activities = []
            local_id_map = {}  # For tracking which local ID corresponds to which batch record
            
            for log in activity_logs:
                try:
                    # Don't include the local numeric ID in the Supabase record
                    # Build a valid Supabase record with fallbacks for missing fields
                    supabase_record = {
                        "id": log["id"], 
                        "user_id": user_id,
                        "org_id": org_id,
                        "window_title": log.get("window_title", "Unknown"),
                        "process_name": log.get("process_name", "Unknown")
                    }
                    
                    # Store local ID mapping for later use when updating sync status
                    local_id = log["id"]
                    
                    # Handle client_created_at with proper ISO format
                    if log.get("created_at"):
                        supabase_record["client_created_at"] = log["created_at"]
                    else:
                        supabase_record["client_created_at"] = datetime.now().isoformat()
                    
                    # Add optional fields only if they exist with proper type conversion
                    if log.get("executable_path"):
                        supabase_record["executable_path"] = log["executable_path"]
                    
                    # Handle timestamps
                    if log.get("start_time"):
                        supabase_record["start_time"] = log["start_time"]
                    
                    if log.get("end_time"):
                        supabase_record["end_time"] = log["end_time"]
                    
                    # Convert duration to integer (required by Supabase schema)
                    if log.get("duration") is not None:
                        # First try to convert to float, then to int
                        try:
                            duration_float = float(log["duration"])
                            # Ensure it's a positive integer by taking absolute value and rounding
                            supabase_record["duration"] = int(abs(duration_float))
                            logger.debug(f"Converted duration from {log['duration']} to {supabase_record['duration']}")
                        except (ValueError, TypeError):
                            logger.warning(f"Could not convert duration to integer: {log['duration']}, omitting field")
                    
                    # Store the record and mapping
                    supabase_activities.append(supabase_record)
                    # Map the position in the batch to the local ID
                    local_id_map[len(supabase_activities) - 1] = local_id
                    
                except Exception as e:
                    logger.error(f"Error preparing activity log {log.get('id')}: {str(e)}")
                    continue
            
            # Split into batches to avoid request size limits
            batch_size = 50
            batches = [supabase_activities[i:i + batch_size] for i in range(0, len(supabase_activities), batch_size)]
            
            synced_count = 0
            failed_count = 0
            
            for batch_index, batch in enumerate(batches):
                try:
                    logger.info(f"Processing activity logs batch {batch_index+1}/{len(batches)} ({len(batch)} items)")
                    
                    # Use Supabase client to insert data
                    result = self.supabase.table("activity_logs").insert(batch).execute()
                    
                    if result and result.data:
                        batch_synced_count = len(result.data)
                        synced_count += batch_synced_count
                        logger.info(f"Successfully synced {batch_synced_count} activity logs to Supabase")
                        
                        # Update local database with sync status using the local ID mapping
                        for i in range(batch_synced_count):
                            try:
                                # Get the batch index which maps to a local ID
                                batch_index = i
                                if batch_index < len(batch):
                                    # Get the local ID that corresponds to this record's position in the batch
                                    batch_position = synced_count - batch_synced_count + i
                                    local_id = local_id_map.get(batch_position % len(batch))
                                    
                                    if local_id:
                                        # Try the update methods with the correct local ID
                                        try:
                                            logger.debug(f"Updating sync status for activity log: {local_id}")
                                            self.db_service.update_activity_log_sync_status(local_id, True)
                                        except AttributeError:
                                            logger.debug("Falling back to update_time_entry_sync_status method")
                                            self.db_service.update_time_entry_sync_status(local_id, True)
                                    else:
                                        logger.warning(f"Could not find local ID mapping for batch position {batch_position}")
                                        
                            except Exception as update_error:
                                logger.error(f"Error updating activity log sync status: {str(update_error)}")
                    else:
                        failed_count += len(batch)
                        logger.error(f"Sync error: No response data for batch {batch_index+1}")
                        
                except Exception as e:
                    failed_count += len(batch)
                    logger.error(f"Batch sync error for batch {batch_index+1}: {str(e)}")
            
            # Update last sync status
            if synced_count > 0:
                self.last_sync["activity_logs"] = {
                    "last_id": activity_logs[-1]["id"],
                    "last_time": datetime.now().isoformat()
                }
                self._save_sync_state()
            
            logger.info(f"Activity logs sync complete: {synced_count} synced, {failed_count} failed")
            
            return {
                "synced": synced_count,
                "failed": failed_count,
                "status": "complete" if failed_count == 0 else "partial"
            }
                
        except Exception as e:
            logger.error(f"Activity logs sync error: {str(e)}")
            import traceback
            logger.error(f"Activity logs sync traceback: {traceback.format_exc()}")
            self.sync_failed = True
            self.sync_error = str(e)
            return {"synced": 0, "failed": len(activity_logs) if 'activity_logs' in locals() else 0, "status": "error"}
            
        finally:
            self.is_syncing = False
            
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
            
            # Helper function to validate timestamps
            def validate_timestamp(timestamp_value: Any) -> str:
                """
                Validate and sanitize a timestamp value.
                If the timestamp is invalid (None, 0, empty string), returns current time in ISO format.
                
                Args:
                    timestamp_value: The timestamp value to validate
                    
                Returns:
                    str: A valid ISO timestamp string
                """
                now = datetime.now().isoformat()
                
                # If timestamp is None, empty string, or 0, return current time
                if timestamp_value is None or timestamp_value == "" or timestamp_value == "0" or timestamp_value == 0:
                    return now
                    
                # If it's already a string, check if it's a valid ISO format
                if isinstance(timestamp_value, str):
                    try:
                        # Try to parse it as datetime to validate
                        datetime.fromisoformat(timestamp_value.replace('Z', '+00:00'))
                        return timestamp_value
                    except ValueError:
                        # If parsing fails, it's not a valid timestamp
                        return now
                
                # For all other cases, return current timestamp
                return now
            
            # Prepare screenshots for Supabase
            supabase_screenshots = []
            for screenshot in screenshots:
                # Get current time once for consistency
                now = datetime.now().isoformat()
                
                # Create a clean record that maps local field names to Supabase field names
                # With timestamp validation
                clean_record = {
                    "id": screenshot["id"],
                    "user_id": user_id,
                    "org_id": self.get_current_org_id(),
                    "image_url": screenshot.get("filepath", ""),  # Map filepath to image_url
                    "taken_at": validate_timestamp(screenshot.get("timestamp") or screenshot.get("created_at")),
                    "created_at": now
                }
                
                # Add optional fields only if they exist
                if screenshot.get("thumbnail_path"):
                    clean_record["thumbnail_url"] = screenshot.get("thumbnail_path")  # Map thumbnail_path to thumbnail_url
                if screenshot.get("activity_log_id"):
                    clean_record["activity_log_id"] = screenshot.get("activity_log_id")
                if screenshot.get("created_at"):
                    clean_record["client_created_at"] = validate_timestamp(screenshot.get("created_at"))
                
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
                    result = self.supabase.table("screenshots").upsert(batch).execute()
                    
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
            
    async def sync_organization_data(self) -> Dict[str, Any]:
        """
        Synchronize organization data from Supabase to local database.
        
        Returns:
            dict: Organization data
        """
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return {"status": "error", "message": "Supabase client not initialized"}
            
        if not self.auth_service.is_authenticated():
            logger.warning("Cannot sync organization data: Not authenticated")
            return {"status": "not_authenticated", "message": "User not authenticated"}
            
        try:
            # Clean up orphaned memberships first
            logger.info("Cleaning up orphaned organization memberships")
            cleanup_result = self.db_service.cleanup_orphaned_memberships()
            if cleanup_result["orphaned_count"] > 0:
                logger.info(f"Cleaned up {cleanup_result['orphaned_count']} orphaned memberships")
            
            # Special handling for known problematic organization ID
            problematic_org_id = "123e4567-e89b-12d3-a456-426614174000"
            logger.info(f"Checking for problematic test organization ID: {problematic_org_id}")
            self.db_service.remove_specific_membership(problematic_org_id)
                
            # Get user data
            user_id = self.auth_service.user.get("id")
            if not user_id:
                logger.error("Cannot sync organization data: User ID not available")
                return {"status": "error", "message": "User ID not available"}
                
            logger.info(f"Starting organization data sync for user: {user_id}")
            
            # Get organization memberships
            try:
                # Use the Supabase client to get memberships
                logger.info(f"Fetching organization memberships for user: {user_id}")
                memberships_result = self.supabase.table("org_members").select("*").eq("user_id", user_id).execute()
                
                # Log raw API response for debugging
                logger.debug(f"Supabase memberships response: {json.dumps(memberships_result.data) if memberships_result.data else 'No data'}")
                
                memberships = memberships_result.data if memberships_result.data else []
                
                if not memberships:
                    logger.info("No organization memberships found for user")
                    return {"status": "no_data", "message": "No organization memberships found"}
                    
                logger.info(f"Found {len(memberships)} organization memberships")
                
                # Filter out memberships with the problematic organization ID
                memberships = [m for m in memberships if m["org_id"] != problematic_org_id]
                if len(memberships_result.data or []) != len(memberships):
                    logger.warning(f"Filtered out membership with problematic org ID: {problematic_org_id}")
                
                # Get organization details
                org_ids = [membership["org_id"] for membership in memberships]
                organizations = []
                failed_org_ids = []
                
                if not org_ids:
                    logger.info("No valid organization IDs found after filtering")
                    return {"status": "no_data", "message": "No valid organization IDs"}
                
                logger.info(f"Fetching details for {len(org_ids)} organizations: {org_ids}")
                
                for org_id in org_ids:
                    logger.info(f"Fetching organization details for: {org_id}")
                    org_result = self.supabase.table("organizations").select("*").eq("id", org_id).execute()
                    
                    if org_result.data and len(org_result.data) > 0:
                        logger.info(f"Successfully retrieved organization: {org_id}")
                        organizations.append(org_result.data[0])
                    else:
                        logger.warning(f"Organization not found in Supabase: {org_id}")
                        failed_org_ids.append(org_id)
                        
                        # Remove memberships for non-existent organizations
                        logger.info(f"Removing membership for non-existent organization: {org_id}")
                        self.db_service.remove_specific_membership(org_id)
                
                if not organizations:
                    logger.warning("No organizations found in Supabase")
                    return {
                        "status": "no_data", 
                        "message": "No organizations found", 
                        "memberships": memberships,
                        "cleaned_up": cleanup_result["orphaned_count"]
                    }
                
                # First store ALL organization data locally - with retries
                successfully_saved_orgs = []
                for org in organizations:
                    # Log the organization data being saved
                    logger.info(f"Saving organization to local database: {org['id']} - {org.get('name', 'No name')}")
                    
                    # Try to save organization with retry logic
                    max_retries = 3
                    saved = False
                    
                    for attempt in range(max_retries):
                        org_saved = self.db_service.save_organization_data(org)
                        if org_saved:
                            logger.info(f"Successfully saved organization: {org['id']}")
                            successfully_saved_orgs.append(org['id'])
                            saved = True
                            break
                        else:
                            logger.warning(f"Failed to save organization (attempt {attempt+1}/{max_retries}): {org['id']}")
                    
                    if not saved:
                        logger.error(f"Failed to save organization after {max_retries} attempts: {org['id']}")
                        failed_org_ids.append(org['id'])
                
                # Filter memberships to only include those with successfully saved organizations
                valid_memberships = [m for m in memberships if m["org_id"] in successfully_saved_orgs]
                invalid_memberships = [m for m in memberships if m["org_id"] not in successfully_saved_orgs]
                
                if invalid_memberships:
                    logger.warning(f"Skipping {len(invalid_memberships)} memberships with invalid organization references")
                    for m in invalid_memberships:
                        logger.debug(f"Skipping membership: org_id={m['org_id']}, user_id={m['user_id']}")
                
                # Now that organizations are saved, save the valid memberships
                successful_memberships = 0
                failed_memberships = 0
                
                for membership in valid_memberships:
                    try:
                        logger.info(f"Saving membership: org_id={membership['org_id']}, user_id={membership['user_id']}")
                        result = self.db_service.save_org_membership(membership)
                        
                        if result:
                            logger.info(f"Successfully saved membership: org_id={membership['org_id']}, user_id={membership['user_id']}")
                            successful_memberships += 1
                        else:
                            logger.warning(f"Failed to save membership: org_id={membership['org_id']}, user_id={membership['user_id']}")
                            failed_memberships += 1
                            
                    except Exception as e:
                        failed_memberships += 1
                        logger.error(f"Error saving membership for org {membership['org_id']}: {str(e)}")
                    
                logger.info(f"Organization data sync summary:")
                logger.info(f"  - Organizations: {len(successfully_saved_orgs)} saved, {len(failed_org_ids)} failed")
                logger.info(f"  - Memberships: {successful_memberships} saved, {failed_memberships} failed")
                logger.info(f"  - Orphaned memberships cleaned up: {cleanup_result['orphaned_count']}")
                
                return {
                    "organizations": organizations,
                    "memberships": memberships,
                    "saved_orgs": len(successfully_saved_orgs),
                    "failed_orgs": len(failed_org_ids),
                    "saved_memberships": successful_memberships,
                    "failed_memberships": failed_memberships,
                    "cleaned_up": cleanup_result["orphaned_count"],
                    "status": "complete" if failed_org_ids == [] and failed_memberships == 0 else "partial"
                }
                
            except Exception as e:
                logger.error(f"Error getting organization data: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return {"status": "error", "message": f"Error getting organization data: {str(e)}"}
                    
        except Exception as e:
            logger.error(f"Organization data sync error: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {"status": "error", "message": f"Sync error: {str(e)}"}
            
    async def sync_clients(self) -> Dict[str, Any]:
        """
        Synchronize clients from local database to Supabase.
        
        Returns:
            dict: Sync results with counts and status
        """
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return {"synced": 0, "failed": 0, "status": "error"}
            
        if not self.auth_service.is_authenticated():
            logger.warning("Cannot sync clients: Not authenticated")
            return {"synced": 0, "failed": 0, "status": "not_authenticated"}
            
        try:
            # Only set is_syncing flag when called directly (not from sync_all)
            if not self.is_syncing:
                self.is_syncing = True
            self.sync_failed = False
            self.sync_error = None
            
            # Get user and organization data
            user_id = self.auth_service.user.get("id")
            org_id = await self._get_user_org_id(user_id)
            
            if not org_id:
                logger.warning("Cannot sync clients: No organization found")
                self.is_syncing = False
                return {"synced": 0, "failed": 0, "status": "no_organization"}
            
            # Get unsynchronized clients
            clients = self.db_service.get_unsynchronized_clients()
            
            if not clients:
                logger.info("No clients to sync")
                return {"synced": 0, "failed": 0, "status": "no_data"}
            
            logger.info(f"Syncing {len(clients)} clients")
            
            # Prepare clients for Supabase with proper field validation
            supabase_clients = []
            local_id_map = {}  # For tracking which local ID maps to which batch record
            skipped_clients = 0
            
            for client in clients:
                try:
                    # Validate user_id is a proper UUID - skip records with invalid user IDs
                    if not client.get("user_id") or not self._is_valid_uuid(client["user_id"]):
                        logger.warning(f"Skipping client {client.get('id')} with invalid user_id: {client.get('user_id')}")
                        skipped_clients += 1
                        continue
                    
                    # Build a valid Supabase record
                    supabase_record = {
                        "id": client["id"],  # Use the same UUID
                        "name": client["name"],
                        "user_id": client["user_id"], # This must be a valid UUID
                        "org_id": org_id,  # Add organization ID for Supabase RLS
                        "created_at": client.get("created_at") or datetime.now().isoformat(),
                        "updated_at": client.get("updated_at") or datetime.now().isoformat(),
                        "is_active": client.get("is_active", 1) == 1,  # Convert to boolean
                    }
                    
                    # Add optional fields only if they exist
                    for field in ["contact_name", "email", "phone", "address", "notes"]:
                        if client.get(field) is not None:
                            supabase_record[field] = client[field]
                    
                    # Store the record and mapping
                    supabase_clients.append(supabase_record)
                    local_id_map[len(supabase_clients) - 1] = client["id"]
                    
                except Exception as e:
                    logger.error(f"Error preparing client {client.get('id')}: {str(e)}")
                    continue
            
            # Split into batches to avoid request size limits
            batch_size = 20
            batches = [supabase_clients[i:i + batch_size] for i in range(0, len(supabase_clients), batch_size)]
            
            synced_count = 0
            failed_count = 0
            
            for batch_index, batch in enumerate(batches):
                try:
                    logger.info(f"Processing clients batch {batch_index+1}/{len(batches)} ({len(batch)} items)")
                    
                    # Use Supabase client to upsert data
                    result = self.supabase.table("clients").upsert(batch).execute()
                    
                    if result and result.data:
                        batch_synced_count = len(result.data)
                        synced_count += batch_synced_count
                        logger.info(f"Successfully synced {batch_synced_count} clients to Supabase")
                        
                        # Update local database with sync status
                        for i in range(batch_synced_count):
                            try:
                                batch_position = synced_count - batch_synced_count + i
                                client_id = local_id_map.get(batch_position % len(batch))
                                if client_id:
                                    self.db_service.update_client_sync_status(client_id, True)
                            except Exception as update_error:
                                logger.error(f"Error updating client sync status: {str(update_error)}")
                    else:
                        failed_count += len(batch)
                        logger.error(f"Sync error: No response data for batch {batch_index+1}")
                except Exception as e:
                    failed_count += len(batch)
                    logger.error(f"Batch sync error for batch {batch_index+1}: {str(e)}")
            
            logger.info(f"Clients sync complete: {synced_count} synced, {failed_count} failed")
            
            return {
                "synced": synced_count,
                "failed": failed_count,
                "status": "complete" if failed_count == 0 else "partial"
            }
                
        except Exception as e:
            logger.error(f"Clients sync error: {str(e)}")
            import traceback
            logger.error(f"Clients sync traceback: {traceback.format_exc()}")
            self.sync_failed = True
            self.sync_error = str(e)
            return {"synced": 0, "failed": len(clients) if 'clients' in locals() else 0, "status": "error"}
            
        finally:
            if not self.is_syncing:
                self.is_syncing = False
                
    async def sync_projects(self) -> Dict[str, Any]:
        """
        Synchronize projects from local database to Supabase.
        
        Returns:
            dict: Sync results with counts and status
        """
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return {"synced": 0, "failed": 0, "status": "error"}
            
        if not self.auth_service.is_authenticated():
            logger.warning("Cannot sync projects: Not authenticated")
            return {"synced": 0, "failed": 0, "status": "not_authenticated"}
            
        try:
            # Only set is_syncing flag when called directly (not from sync_all)
            if not self.is_syncing:
                self.is_syncing = True
            self.sync_failed = False
            self.sync_error = None
            
            # Get user and organization data
            user_id = self.auth_service.user.get("id")
            org_id = await self._get_user_org_id(user_id)
            
            if not org_id:
                logger.warning("Cannot sync projects: No organization found")
                self.is_syncing = False
                return {"synced": 0, "failed": 0, "status": "no_organization"}
            
            # Get unsynchronized projects
            projects = self.db_service.get_unsynchronized_projects()
            
            if not projects:
                logger.info("No projects to sync")
                return {"synced": 0, "failed": 0, "status": "no_data"}
            
            logger.info(f"Syncing {len(projects)} projects")
            
            # Prepare projects for Supabase with proper field validation
            supabase_projects = []
            local_id_map = {}  # For tracking which local ID maps to which batch record
            
            for project in projects:
                try:
                    # Build a valid Supabase record
                    supabase_record = {
                        "id": project["id"],  # Use the same UUID
                        "name": project["name"],
                        "user_id": project["user_id"],
                        "org_id": org_id,  # Add organization ID for Supabase RLS
                        "created_at": project.get("created_at") or datetime.now().isoformat(),
                        "updated_at": project.get("updated_at") or datetime.now().isoformat(),
                        "is_active": project.get("is_active", 1) == 1,  # Convert to boolean
                        "is_billable": project.get("is_billable", 1) == 1,  # Convert to boolean
                    }
                    
                    # Add optional fields only if they exist
                    for field in ["client_id", "description", "color", "hourly_rate"]:
                        if project.get(field) is not None:
                            supabase_record[field] = project[field]
                    
                    # Store the record and mapping
                    supabase_projects.append(supabase_record)
                    local_id_map[len(supabase_projects) - 1] = project["id"]
                    
                except Exception as e:
                    logger.error(f"Error preparing project {project.get('id')}: {str(e)}")
                    continue
            
            # Split into batches to avoid request size limits
            batch_size = 20
            batches = [supabase_projects[i:i + batch_size] for i in range(0, len(supabase_projects), batch_size)]
            
            synced_count = 0
            failed_count = 0
            
            for batch_index, batch in enumerate(batches):
                try:
                    logger.info(f"Processing projects batch {batch_index+1}/{len(batches)} ({len(batch)} items)")
                    
                    # Use Supabase client to upsert data
                    result = self.supabase.table("projects").upsert(batch).execute()
                    
                    if result and result.data:
                        batch_synced_count = len(result.data)
                        synced_count += batch_synced_count
                        logger.info(f"Successfully synced {batch_synced_count} projects to Supabase")
                        
                        # Update local database with sync status
                        for i in range(batch_synced_count):
                            try:
                                batch_position = synced_count - batch_synced_count + i
                                project_id = local_id_map.get(batch_position % len(batch))
                                if project_id:
                                    self.db_service.update_project_sync_status(project_id, True)
                            except Exception as update_error:
                                logger.error(f"Error updating project sync status: {str(update_error)}")
                    else:
                        failed_count += len(batch)
                        logger.error(f"Sync error: No response data for batch {batch_index+1}")
                except Exception as e:
                    failed_count += len(batch)
                    logger.error(f"Batch sync error for batch {batch_index+1}: {str(e)}")
            
            logger.info(f"Projects sync complete: {synced_count} synced, {failed_count} failed")
            
            return {
                "synced": synced_count,
                "failed": failed_count,
                "status": "complete" if failed_count == 0 else "partial"
            }
                
        except Exception as e:
            logger.error(f"Projects sync error: {str(e)}")
            import traceback
            logger.error(f"Projects sync traceback: {traceback.format_exc()}")
            self.sync_failed = True
            self.sync_error = str(e)
            return {"synced": 0, "failed": len(projects) if 'projects' in locals() else 0, "status": "error"}
            
        finally:
            if not self.is_syncing:
                self.is_syncing = False

    async def sync_tasks(self) -> Dict[str, Any]:
        """
        Synchronize project tasks from local database to Supabase.
        
        Returns:
            dict: Sync results with counts and status
        """
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return {"synced": 0, "failed": 0, "status": "error"}
            
        if not self.auth_service.is_authenticated():
            logger.warning("Cannot sync project tasks: Not authenticated")
            return {"synced": 0, "failed": 0, "status": "not_authenticated"}
            
        try:
            # Only set is_syncing flag when called directly (not from sync_all)
            if not self.is_syncing:
                self.is_syncing = True
            self.sync_failed = False
            self.sync_error = None
            
            # Get user and organization data
            user_id = self.auth_service.user.get("id")
            org_id = await self._get_user_org_id(user_id)
            
            if not org_id:
                logger.warning("Cannot sync project tasks: No organization found")
                self.is_syncing = False
                return {"synced": 0, "failed": 0, "status": "no_organization"}
            
            # Get unsynchronized project tasks
            tasks = self.db_service.get_unsynchronized_project_tasks()
            
            if not tasks:
                logger.info("No project tasks to sync")
                return {"synced": 0, "failed": 0, "status": "no_data"}
            
            logger.info(f"Syncing {len(tasks)} project tasks")
            
            # Prepare project tasks for Supabase with proper field validation
            supabase_tasks = []
            local_id_map = {}  # For tracking which local ID maps to which batch record
            
            for task in tasks:
                try:
                    # Build a valid Supabase record based on project_tasks schema
                    # Note: org_id field removed as it doesn't exist in Supabase schema
                    supabase_record = {
                        "id": task["id"],  # Use the same UUID
                        "name": task["name"],
                        "description": task.get("description"),
                        "project_id": task["project_id"],
                        "created_at": task.get("created_at") or datetime.now().isoformat(),
                        "updated_at": task.get("updated_at") or datetime.now().isoformat(),
                        "is_active": task.get("is_active", 1) == 1,  # Convert to boolean
                    }
                    
                    # Add optional fields only if they exist
                    if task.get("estimated_hours") is not None:
                        supabase_record["estimated_hours"] = task["estimated_hours"]
                    
                    # Store the record and mapping
                    supabase_tasks.append(supabase_record)
                    local_id_map[len(supabase_tasks) - 1] = task["id"]
                    
                except Exception as e:
                    logger.error(f"Error preparing project task {task.get('id')}: {str(e)}")
                    continue
            
            # Split into batches to avoid request size limits
            batch_size = 20
            batches = [supabase_tasks[i:i + batch_size] for i in range(0, len(supabase_tasks), batch_size)]
            
            synced_count = 0
            failed_count = 0
            
            for batch_index, batch in enumerate(batches):
                try:
                    logger.info(f"Processing project tasks batch {batch_index+1}/{len(batches)} ({len(batch)} items)")
                    
                    # Use Supabase client to upsert data
                    result = self.supabase.table("project_tasks").upsert(batch).execute()
                    
                    if result and result.data:
                        batch_synced_count = len(result.data)
                        synced_count += batch_synced_count
                        logger.info(f"Successfully synced {batch_synced_count} project tasks to Supabase")
                        
                        # Update local database with sync status
                        for i in range(batch_synced_count):
                            try:
                                batch_position = synced_count - batch_synced_count + i
                                task_id = local_id_map.get(batch_position % len(batch))
                                if task_id:
                                    self.db_service.update_project_task_sync_status(task_id, True)
                            except Exception as update_error:
                                logger.error(f"Error updating project task sync status: {str(update_error)}")
                    else:
                        failed_count += len(batch)
                        logger.error(f"Sync error: No response data for batch {batch_index+1}")
                except Exception as e:
                    failed_count += len(batch)
                    logger.error(f"Batch sync error for batch {batch_index+1}: {str(e)}")
            
            logger.info(f"Project tasks sync complete: {synced_count} synced, {failed_count} failed")
            
            return {
                "synced": synced_count,
                "failed": failed_count,
                "status": "complete" if failed_count == 0 else "partial"
            }
                
        except Exception as e:
            logger.error(f"Project tasks sync error: {str(e)}")
            import traceback
            logger.error(f"Project tasks sync traceback: {traceback.format_exc()}")
            self.sync_failed = True
            self.sync_error = str(e)
            return {"synced": 0, "failed": len(tasks) if 'tasks' in locals() else 0, "status": "error"}
            
        finally:
            if not self.is_syncing:
                self.is_syncing = False
    
    async def sync_time_entries(self) -> Dict[str, Any]:
        """
        Synchronize time entries from local database to Supabase.
        
        Returns:
            dict: Sync results with counts and status
        """
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return {"synced": 0, "failed": 0, "status": "error"}
            
        if not self.auth_service.is_authenticated():
            logger.warning("Cannot sync time entries: Not authenticated")
            return {"synced": 0, "failed": 0, "status": "not_authenticated"}
            
        try:
            # Only set is_syncing flag when called directly (not from sync_all)
            if not self.is_syncing:
                self.is_syncing = True
            self.sync_failed = False
            self.sync_error = None
            
            # Get user and organization data
            user_id = self.auth_service.user.get("id")
            org_id = await self._get_user_org_id(user_id)
            
            if not org_id:
                logger.warning("Cannot sync time entries: No organization found")
                self.is_syncing = False
                return {"synced": 0, "failed": 0, "status": "no_organization"}
            
            # Get unsynchronized time entries
            time_entries = self.db_service.get_unsynchronized_time_entries()
            
            if not time_entries:
                logger.info("No time entries to sync")
                return {"synced": 0, "failed": 0, "status": "no_data"}
            
            logger.info(f"Syncing {len(time_entries)} time entries")
            
            # Prepare time entries for Supabase with proper field validation
            supabase_entries = []
            local_id_map = {}  # For tracking which local ID maps to which batch record
            
            for entry in time_entries:
                try:
                    # Ensure entry has required fields
                    if not entry.get("start_time"):
                        logger.warning(f"Skipping time entry {entry.get('id')} - missing start_time")
                        continue
                    
                    # Build a valid Supabase record
                    supabase_record = {
                        "id": entry["id"],  # Use the same UUID
                        "user_id": entry["user_id"],
                        "org_id": org_id,  # Add organization ID for Supabase RLS
                        "start_time": entry["start_time"],
                        "created_at": entry.get("created_at") or datetime.now().isoformat(),
                        "updated_at": entry.get("updated_at") or datetime.now().isoformat(),
                        "is_active": entry.get("is_active", 0) == 1,  # Convert to boolean
                    }
                    
                    # Add optional fields only if they exist
                    for field in ["project_id", "task_id", "description", "end_time"]:
                        if entry.get(field) is not None:
                            supabase_record[field] = entry[field]
                    
                    # Add duration if available and valid
                    if entry.get("duration") is not None:
                        # Ensure duration is a positive integer
                        try:
                            duration = int(entry["duration"])
                            if duration < 0:
                                duration = abs(duration)
                            supabase_record["duration"] = duration
                        except (ValueError, TypeError):
                            # If duration can't be converted, calculate it from start/end time
                            if entry.get("end_time") and entry.get("start_time"):
                                try:
                                    start = datetime.fromisoformat(entry["start_time"].replace("Z", "+00:00"))
                                    end = datetime.fromisoformat(entry["end_time"].replace("Z", "+00:00"))
                                    supabase_record["duration"] = int((end - start).total_seconds())
                                except (ValueError, TypeError):
                                    logger.warning(f"Could not calculate duration for time entry {entry.get('id')}")
                    
                    # Store the record and mapping
                    supabase_entries.append(supabase_record)
                    local_id_map[len(supabase_entries) - 1] = entry["id"]
                    
                except Exception as e:
                    logger.error(f"Error preparing time entry {entry.get('id')}: {str(e)}")
                    continue
            
            # Split into batches to avoid request size limits
            batch_size = 20
            batches = [supabase_entries[i:i + batch_size] for i in range(0, len(supabase_entries), batch_size)]
            
            synced_count = 0
            failed_count = 0
            
            for batch_index, batch in enumerate(batches):
                try:
                    logger.info(f"Processing time entries batch {batch_index+1}/{len(batches)} ({len(batch)} items)")
                    
                    # Use Supabase client to upsert data
                    result = self.supabase.table("time_entries").upsert(batch).execute()
                    
                    if result and result.data:
                        batch_synced_count = len(result.data)
                        synced_count += batch_synced_count
                        logger.info(f"Successfully synced {batch_synced_count} time entries to Supabase")
                        
                        # Update local database with sync status
                        for i in range(batch_synced_count):
                            try:
                                batch_position = synced_count - batch_synced_count + i
                                entry_id = local_id_map.get(batch_position % len(batch))
                                if entry_id:
                                    self.db_service.update_time_entry_sync_status(entry_id, True)
                            except Exception as update_error:
                                logger.error(f"Error updating time entry sync status: {str(update_error)}")
                    else:
                        failed_count += len(batch)
                        logger.error(f"Sync error: No response data for batch {batch_index+1}")
                except Exception as e:
                    failed_count += len(batch)
                    logger.error(f"Batch sync error for batch {batch_index+1}: {str(e)}")
            
            logger.info(f"Time entries sync complete: {synced_count} synced, {failed_count} failed")
            
            return {
                "synced": synced_count,
                "failed": failed_count,
                "status": "complete" if failed_count == 0 else "partial"
            }
                
        except Exception as e:
            logger.error(f"Time entries sync error: {str(e)}")
            import traceback
            logger.error(f"Time entries sync traceback: {traceback.format_exc()}")
            self.sync_failed = True
            self.sync_error = str(e)
            return {"synced": 0, "failed": len(time_entries) if 'time_entries' in locals() else 0, "status": "error"}
            
        finally:
            if not self.is_syncing:
                self.is_syncing = False

    async def sync_all(self) -> Dict[str, Any]:
        """
        Synchronize all data between local and remote.
        
        Returns:
            dict: Sync results
        """
        # Check if already syncing to prevent duplicate requests
        if self.is_syncing:
            logger.warning("Sync already in progress - sync_all called again while syncing")
            return {"status": "in_progress", "message": "Sync already in progress"}
            
        if not self.auth_service.is_authenticated():
            logger.warning("Cannot sync: Not authenticated")
            return {"status": "not_authenticated", "message": "User not authenticated"}
            
        # Reset error state
        self.sync_failed = False
        self.sync_error = None
            
        # Set global sync flag
        try:
            # Set sync flag before starting
            self.is_syncing = True
            logger.info("Starting full sync operation")
            
            # Track timing for diagnostics
            start_time = datetime.now()
            
            # Track individual component results
            org_result = None
            activity_result = None
            screenshot_result = None
            client_result = None
            project_result = None
            task_result = None
            time_entry_result = None
            
            try:
                # Sync organization data first (pull)
                logger.info("Starting organization data sync")
                org_start = datetime.now()
                org_result = await self.sync_organization_data()
                org_duration = (datetime.now() - org_start).total_seconds()
                logger.info(f"Organization sync completed in {org_duration:.2f}s with status: {org_result.get('status', 'unknown')}")
                
                # If org sync failed completely, this might be why foreign key constraints fail
                if org_result.get('status') == 'error':
                    logger.error("Organization sync failed - this might cause issues with other sync operations")
                
                # Sync activity logs (push) only if not already syncing
                # Each individual sync method has its own check for is_syncing
                logger.info("Starting activity logs sync")
                activity_start = datetime.now()
                activity_result = await self.sync_activity_logs()
                activity_duration = (datetime.now() - activity_start).total_seconds()
                logger.info(f"Activity logs sync completed in {activity_duration:.2f}s with status: {activity_result.get('status', 'unknown')}")
                
                # Sync screenshots (push)
                logger.info("Starting screenshots sync")
                screenshot_start = datetime.now()
                screenshot_result = await self.sync_screenshots()
                screenshot_duration = (datetime.now() - screenshot_start).total_seconds()
                logger.info(f"Screenshots sync completed in {screenshot_duration:.2f}s with status: {screenshot_result.get('status', 'unknown')}")
                
                # Sync clients (push)
                logger.info("Starting clients sync")
                client_start = datetime.now()
                client_result = await self.sync_clients()
                client_duration = (datetime.now() - client_start).total_seconds()
                logger.info(f"Clients sync completed in {client_duration:.2f}s with status: {client_result.get('status', 'unknown')}")
                
                # Sync projects (push)
                logger.info("Starting projects sync")
                project_start = datetime.now()
                project_result = await self.sync_projects()
                project_duration = (datetime.now() - project_start).total_seconds()
                logger.info(f"Projects sync completed in {project_duration:.2f}s with status: {project_result.get('status', 'unknown')}")
                
                # Sync tasks (push)
                logger.info("Starting tasks sync")
                task_start = datetime.now()
                task_result = await self.sync_tasks()
                task_duration = (datetime.now() - task_start).total_seconds()
                logger.info(f"Tasks sync completed in {task_duration:.2f}s with status: {task_result.get('status', 'unknown')}")

                # Sync time entries (push)
                logger.info("Starting time entries sync")
                time_entry_start = datetime.now()
                time_entry_result = await self.sync_time_entries()
                time_entry_duration = (datetime.now() - time_entry_start).total_seconds()
                logger.info(f"Time entries sync completed in {time_entry_duration:.2f}s with status: {time_entry_result.get('status', 'unknown')}")
                
                # Calculate overall duration
                total_duration = (datetime.now() - start_time).total_seconds()
                
                # Determine overall status
                statuses = [
                    org_result.get('status') if org_result else 'error',
                    activity_result.get('status') if activity_result else 'error',
                    screenshot_result.get('status') if screenshot_result else 'error',
                    client_result.get('status') if client_result else 'error',
                    project_result.get('status') if project_result else 'error',
                    task_result.get('status') if task_result else 'error',
                    time_entry_result.get('status') if time_entry_result else 'error'
                ]
                
                overall_status = "complete"
                if "error" in statuses:
                    overall_status = "error"
                elif "partial" in statuses:
                    overall_status = "partial"
                
                logger.info(f"Full sync completed in {total_duration:.2f}s with status: {overall_status}")
                
                return {
                    "organization": org_result,
                    "activity_logs": activity_result,
                    "screenshots": screenshot_result,
                    "clients": client_result,
                    "projects": project_result,
                    "tasks": task_result,
                    "time_entries": time_entry_result,
                    "duration_seconds": total_duration,
                    "status": overall_status
                }
                
            except Exception as component_error:
                # This catches errors in the individual sync operations
                logger.error(f"Component sync error: {str(component_error)}")
                import traceback
                logger.error(f"Component sync traceback: {traceback.format_exc()}")
                
                # Set error state
                self.sync_failed = True
                self.sync_error = str(component_error)
                
                # Return partial results
                return {
                    "organization": org_result,
                    "activity_logs": activity_result,
                    "screenshots": screenshot_result,
                    "error": str(component_error),
                    "status": "error"
                }
                
        except Exception as e:
            # This catches errors in the overall sync_all operation
            logger.error(f"Sync all error: {str(e)}")
            import traceback
            logger.error(f"Sync all traceback: {traceback.format_exc()}")
            
            # Set error state
            self.sync_failed = True
            self.sync_error = str(e)
            return {
                "status": "error", 
                "message": f"Sync all error: {str(e)}"
            }
            
        finally:
            # Always reset sync flag
            logger.info("Resetting sync flag")
            self.is_syncing = False
            
    async def _get_user_org_id(self, user_id: str) -> Optional[str]:
        """
        Get the user's organization ID.
        
        Args:
            user_id: The user ID
            
        Returns:
            str: Organization ID or None if not found
        """
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return None
            
        try:
            # First check local storage
            org_membership = self.db_service.get_user_org_membership(user_id)
            if org_membership:
                logger.info(f"Found local organization membership for user {user_id}: {org_membership['org_id']}")
                return org_membership["org_id"]
                
            # If not found locally, fetch from Supabase
            try:
                # Use Supabase client to get user's org memberships
                logger.info(f"Fetching organization memberships for user {user_id} from Supabase")
                result = self.supabase.table("org_members").select("*").eq("user_id", user_id).execute()
                
                if not result.data:
                    logger.warning(f"No organization memberships found for user {user_id}")
                    return None
                    
                memberships = result.data
                logger.info(f"Found {len(memberships)} organization memberships in Supabase")
                
                # Get organization details for each membership
                for membership in memberships:
                    org_id = membership["org_id"]
                    
                    # Get organization details from Supabase
                    logger.info(f"Fetching organization {org_id} details from Supabase")
                    org_result = self.supabase.table("organizations").select("*").eq("id", org_id).execute()
                    
                    if org_result.data and len(org_result.data) > 0:
                        # Save organization to local database first
                        org_data = org_result.data[0]
                        logger.info(f"Saving organization {org_id} to local database")
                        saved = self.db_service.save_organization_data(org_data)
                        
                        if not saved:
                            logger.error(f"Failed to save organization {org_id} to local database")
                            continue
                        
                        # Now save the membership
                        logger.info(f"Saving membership for organization {org_id}")
                        self.db_service.save_org_membership(membership)
                    else:
                        logger.warning(f"Organization {org_id} not found in Supabase")
                
                # Return the first valid organization ID
                if memberships:
                    logger.info(f"Using organization {memberships[0]['org_id']} for user {user_id}")
                    return memberships[0]["org_id"]
                    
                return None
            except Exception as e:
                logger.error(f"Error fetching organization data: {str(e)}")
                return None
                    
        except Exception as e:
            logger.error(f"Error getting organization ID: {str(e)}")
            return None
            
    # Helper method to get the current organization ID
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
            
    # The _bucket_exists and _create_bucket methods have been replaced by direct Supabase client calls
            
    def _load_sync_state(self) -> None:
        """
        Load the last sync state from file.
        """
        try:
            config_dir = os.path.expanduser("~/TimeTracker/data")
            sync_file = os.path.join(config_dir, "sync_state.json")
            
            if not os.path.exists(sync_file):
                self.last_sync = {}
                return
                
            with open(sync_file, "r") as f:
                self.last_sync = json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading sync state: {str(e)}")
            self.last_sync = {}
            
    def _save_sync_state(self) -> None:
        """
        Save the last sync state to file.
        """
        try:
            config_dir = os.path.expanduser("~/TimeTracker/data")
            os.makedirs(config_dir, exist_ok=True)
            
            sync_file = os.path.join(config_dir, "sync_state.json")
            
            with open(sync_file, "w") as f:
                json.dump(self.last_sync, f)
                
        except Exception as e:
            logger.error(f"Error saving sync state: {str(e)}")
            
    def _is_valid_uuid(self, uuid_string: str) -> bool:
        """
        Check if a string is a valid UUID.
        
        Args:
            uuid_string: The string to check
            
        Returns:
            bool: True if the string is a valid UUID
        """
        if not uuid_string:
            return False
            
        try:
            # Convert to standard UUID format
            uuid_obj = uuid.UUID(uuid_string)
            # Check that it's not a UUID like "00000000-0000-0000-0000-000000000000"
            if uuid_obj.int == 0:
                return False
            return True
        except (ValueError, AttributeError, TypeError):
            return False
