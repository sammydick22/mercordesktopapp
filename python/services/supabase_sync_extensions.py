"""
Extensions for SupabaseSyncService to support clients, projects, and tasks synchronization.
"""
import logging
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

# Setup logger
logger = logging.getLogger(__name__)

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
        
        # Get last client sync ID
        last_sync_id = self.last_sync.get("clients", {}).get("last_id", '')
        
        # Get unsynchronized clients
        clients = self.db_service.get_unsynchronized_clients(last_sync_id)
        
        if not clients:
            logger.info("No clients to sync")
            self.is_syncing = False
            return {"synced": 0, "failed": 0, "status": "no_data"}
        
        logger.info(f"Syncing {len(clients)} clients")
        
        # Prepare clients for Supabase
        supabase_clients = []
        for client in clients:
            supabase_clients.append({
                "id": client["id"],
                "user_id": user_id,
                "org_id": org_id,
                "name": client["name"],
                "contact_name": client["contact_name"],
                "email": client["email"],
                "phone": client["phone"],
                "address": client["address"],
                "notes": client["notes"],
                "is_active": client["is_active"],
                "created_at": client["created_at"],
                "updated_at": client["updated_at"] or datetime.now().isoformat()
            })
        
        # Split into batches to avoid request size limits
        batch_size = 20
        batches = [supabase_clients[i:i + batch_size] for i in range(0, len(supabase_clients), batch_size)]
        
        synced_count = 0
        failed_count = 0
        
        for batch in batches:
            try:
                # Use Supabase client to upsert data (insert or update)
                result = self.supabase.table("clients").upsert(batch).execute()
                
                if result and result.data:
                    synced_ids = [item["id"] for item in result.data]
                    synced_count += len(synced_ids)
                    
                    # Update local database with sync status
                    for client_id in synced_ids:
                        self.db_service.update_client_sync_status(client_id, True)
                else:
                    failed_count += len(batch)
                    logger.error(f"Sync error: No response data")
                    
            except Exception as e:
                failed_count += len(batch)
                logger.error(f"Batch sync error: {str(e)}")
        
        # Update last sync status
        if synced_count > 0:
            self.last_sync["clients"] = {
                "last_id": clients[-1]["id"],
                "last_time": datetime.now().isoformat()
            }
            self._save_sync_state()
        
        logger.info(f"Clients sync complete: {synced_count} synced, {failed_count} failed")
        
        return {
            "synced": synced_count,
            "failed": failed_count,
            "status": "complete" if failed_count == 0 else "partial"
        }
            
    except Exception as e:
        logger.error(f"Clients sync error: {str(e)}")
        self.sync_failed = True
        self.sync_error = str(e)
        return {"synced": 0, "failed": len(clients) if 'clients' in locals() else 0, "status": "error"}
        
    finally:
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
        
        # Get last project sync ID
        last_sync_id = self.last_sync.get("projects", {}).get("last_id", '')
        
        # Get unsynchronized projects
        projects = self.db_service.get_unsynchronized_projects(last_sync_id)
        
        if not projects:
            logger.info("No projects to sync")
            self.is_syncing = False
            return {"synced": 0, "failed": 0, "status": "no_data"}
        
        logger.info(f"Syncing {len(projects)} projects")
        
        # Prepare projects for Supabase
        supabase_projects = []
        for project in projects:
            supabase_projects.append({
                "id": project["id"],
                "user_id": user_id,
                "org_id": org_id,
                "name": project["name"],
                "description": project["description"],
                "client_id": project["client_id"],
                "color": project["color"],
                "hourly_rate": project["hourly_rate"],
                "is_billable": project["is_billable"],
                "is_active": project["is_active"],
                "created_at": project["created_at"],
                "updated_at": project["updated_at"] or datetime.now().isoformat()
            })
        
        # Split into batches to avoid request size limits
        batch_size = 20
        batches = [supabase_projects[i:i + batch_size] for i in range(0, len(supabase_projects), batch_size)]
        
        synced_count = 0
        failed_count = 0
        
        for batch in batches:
            try:
                # Use Supabase client to upsert data (insert or update)
                result = self.supabase.table("projects").upsert(batch).execute()
                
                if result and result.data:
                    synced_ids = [item["id"] for item in result.data]
                    synced_count += len(synced_ids)
                    
                    # Update local database with sync status
                    for project_id in synced_ids:
                        self.db_service.update_project_sync_status(project_id, True)
                else:
                    failed_count += len(batch)
                    logger.error(f"Sync error: No response data")
                    
            except Exception as e:
                failed_count += len(batch)
                logger.error(f"Batch sync error: {str(e)}")
        
        # Update last sync status
        if synced_count > 0:
            self.last_sync["projects"] = {
                "last_id": projects[-1]["id"],
                "last_time": datetime.now().isoformat()
            }
            self._save_sync_state()
        
        logger.info(f"Projects sync complete: {synced_count} synced, {failed_count} failed")
        
        return {
            "synced": synced_count,
            "failed": failed_count,
            "status": "complete" if failed_count == 0 else "partial"
        }
            
    except Exception as e:
        logger.error(f"Projects sync error: {str(e)}")
        self.sync_failed = True
        self.sync_error = str(e)
        return {"synced": 0, "failed": len(projects) if 'projects' in locals() else 0, "status": "error"}
        
    finally:
        self.is_syncing = False

# Task synchronization for a specific project
async def sync_project_tasks(self, project_id: str) -> Dict[str, Any]:
    """
    Synchronize tasks for a specific project from local database to Supabase.
    
    Args:
        project_id: ID of the project to sync tasks for
        
    Returns:
        dict: Sync results with counts and status
    """
    if not self.supabase:
        logger.error("Supabase client not initialized")
        return {"synced": 0, "failed": 0, "status": "error"}
        
    if not self.auth_service.is_authenticated():
        logger.warning("Cannot sync tasks: Not authenticated")
        return {"synced": 0, "failed": 0, "status": "not_authenticated"}
        
    try:
        # Get tasks for the project
        tasks = self.db_service.get_project_tasks(project_id)
        
        if not tasks:
            logger.info(f"No tasks to sync for project {project_id}")
            return {"synced": 0, "failed": 0, "status": "no_data"}
        
        logger.info(f"Syncing {len(tasks)} tasks for project {project_id}")
        
        # Prepare tasks for Supabase
        supabase_tasks = []
        for task in tasks:
            supabase_tasks.append({
                "id": task["id"],
                "name": task["name"],
                "description": task["description"],
                "project_id": task["project_id"],
                "estimated_hours": task["estimated_hours"],
                "is_active": task["is_active"],
                "created_at": task["created_at"],
                "updated_at": task["updated_at"] or datetime.now().isoformat()
            })
        
        # Split into batches to avoid request size limits
        batch_size = 20
        batches = [supabase_tasks[i:i + batch_size] for i in range(0, len(supabase_tasks), batch_size)]
        
        synced_count = 0
        failed_count = 0
        
        for batch in batches:
            try:
                # Use Supabase client to upsert data (insert or update)
                result = self.supabase.table("project_tasks").upsert(batch).execute()
                
                if result and result.data:
                    synced_count += len(result.data)
                else:
                    failed_count += len(batch)
                    logger.error(f"Sync error: No response data")
                    
            except Exception as e:
                failed_count += len(batch)
                logger.error(f"Batch sync error: {str(e)}")
        
        logger.info(f"Tasks sync complete for project {project_id}: {synced_count} synced, {failed_count} failed")
        
        return {
            "synced": synced_count,
            "failed": failed_count,
            "status": "complete" if failed_count == 0 else "partial"
        }
            
    except Exception as e:
        logger.error(f"Tasks sync error for project {project_id}: {str(e)}")
        return {"synced": 0, "failed": len(tasks) if 'tasks' in locals() else 0, "status": "error"}

# New method: Sync all project tasks
async def sync_all_project_tasks(self) -> Dict[str, Any]:
    """
    Synchronize all project tasks from local database to Supabase.
    
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
        
        # Get last task sync ID
        last_sync_id = self.last_sync.get("project_tasks", {}).get("last_id", '')
        
        # Get unsynchronized tasks
        try:
            tasks = self.db_service.get_unsynchronized_project_tasks(last_sync_id)
        except AttributeError:
            logger.warning("Database service doesn't have get_unsynchronized_project_tasks method")
            self.is_syncing = False
            return {"synced": 0, "failed": 0, "status": "error"}
        
        if not tasks:
            logger.info("No project tasks to sync")
            self.is_syncing = False
            return {"synced": 0, "failed": 0, "status": "no_data"}
        
        logger.info(f"Syncing {len(tasks)} project tasks")
        
        # Prepare tasks for Supabase
        supabase_tasks = []
        for task in tasks:
            supabase_tasks.append({
                "id": task["id"],
                "name": task["name"],
                "description": task["description"],
                "project_id": task["project_id"],
                "estimated_hours": task["estimated_hours"],
                "is_active": task["is_active"],
                "created_at": task["created_at"],
                "updated_at": task["updated_at"] or datetime.now().isoformat()
            })
        
        # Split into batches to avoid request size limits
        batch_size = 20
        batches = [supabase_tasks[i:i + batch_size] for i in range(0, len(supabase_tasks), batch_size)]
        
        synced_count = 0
        failed_count = 0
        
        for batch in batches:
            try:
                # Use Supabase client to upsert data (insert or update)
                result = self.supabase.table("project_tasks").upsert(batch).execute()
                
                if result and result.data:
                    synced_ids = [item["id"] for item in result.data]
                    synced_count += len(synced_ids)
                    
                    # Update local database with sync status
                    for task_id in synced_ids:
                        try:
                            self.db_service.update_project_task_sync_status(task_id, True)
                        except AttributeError:
                            logger.warning(f"Database service doesn't have update_project_task_sync_status method")
                else:
                    failed_count += len(batch)
                    logger.error(f"Sync error: No response data")
                    
            except Exception as e:
                failed_count += len(batch)
                logger.error(f"Batch sync error: {str(e)}")
        
        # Update last sync status
        if synced_count > 0:
            self.last_sync["project_tasks"] = {
                "last_id": tasks[-1]["id"],
                "last_time": datetime.now().isoformat()
            }
            self._save_sync_state()
        
        logger.info(f"Project tasks sync complete: {synced_count} synced, {failed_count} failed")
        
        return {
            "synced": synced_count,
            "failed": failed_count,
            "status": "complete" if failed_count == 0 else "partial"
        }
            
    except Exception as e:
        logger.error(f"Project tasks sync error: {str(e)}")
        self.sync_failed = True
        self.sync_error = str(e)
        return {"synced": 0, "failed": len(tasks) if 'tasks' in locals() else 0, "status": "error"}
        
    finally:
        self.is_syncing = False
        
# New method: Sync user profiles
async def sync_user_profiles(self) -> Dict[str, Any]:
    """
    Synchronize user profiles from local database to Supabase.
    
    Returns:
        dict: Sync results with counts and status
    """
    if not self.supabase:
        logger.error("Supabase client not initialized")
        return {"synced": 0, "failed": 0, "status": "error"}
        
    if not self.auth_service.is_authenticated():
        logger.warning("Cannot sync user profiles: Not authenticated")
        return {"synced": 0, "failed": 0, "status": "not_authenticated"}
        
    try:
        # Only set is_syncing flag when called directly (not from sync_all)
        if not self.is_syncing:
            self.is_syncing = True
        self.sync_failed = False
        self.sync_error = None
        
        # Get user ID
        user_id = self.auth_service.user.get("id")
        
        # Get last profile sync ID
        last_sync_id = self.last_sync.get("user_profiles", {}).get("last_id", '')
        
        # Get unsynchronized profiles
        try:
            profiles = self.db_service.get_unsynchronized_user_profiles(last_sync_id)
        except AttributeError:
            logger.warning("Database service doesn't have get_unsynchronized_user_profiles method")
            self.is_syncing = False
            return {"synced": 0, "failed": 0, "status": "error"}
        
        if not profiles:
            logger.info("No user profiles to sync")
            self.is_syncing = False
            return {"synced": 0, "failed": 0, "status": "no_data"}
        
        logger.info(f"Syncing {len(profiles)} user profiles")
        
        # Prepare profiles for Supabase - mapping local fields to Supabase schema
        supabase_profiles = []
        for profile in profiles:
            # Only sync current user's profile
            profile_user_id = profile.get("user_id") or profile.get("id")
            if profile_user_id == user_id:
                # Create a profile object with correct Supabase fields
                supabase_profile = {
                    "id": profile.get("id") or user_id,  # Use ID from profile or user_id
                    "full_name": profile.get("full_name") or profile.get("display_name") or profile.get("name", ""),
                    "avatar_url": profile.get("avatar_url", ""),
                    "role": profile.get("role", "employee"),  # Must be one of: 'admin', 'manager', 'employee'
                    "timezone": profile.get("timezone", "UTC"),
                    "created_at": profile.get("created_at") or datetime.now().isoformat(),
                    "updated_at": profile.get("updated_at") or datetime.now().isoformat()
                }
                supabase_profiles.append(supabase_profile)
        
        if not supabase_profiles:
            logger.info("No user profiles to sync for current user")
            self.is_syncing = False
            return {"synced": 0, "failed": 0, "status": "no_data"}
        
        # Split into batches to avoid request size limits
        batch_size = 20
        batches = [supabase_profiles[i:i + batch_size] for i in range(0, len(supabase_profiles), batch_size)]
        
        synced_count = 0
        failed_count = 0
        
        for batch in batches:
            try:
                # Use Supabase client to upsert data (insert or update)
                result = self.supabase.table("user_profiles").upsert(batch).execute()
                
                if result and result.data:
                    synced_count += len(result.data)
                    logger.info(f"Successfully synced {len(result.data)} user profiles to Supabase")
                    
                    # Update local database with sync status
                    for item in result.data:
                        try:
                            # Make sure we have a valid ID
                            profile_id = item.get("id")
                            if profile_id:
                                logger.info(f"Updating sync status for profile: {profile_id}")
                                self.db_service.update_user_profile_sync_status(profile_id, True)
                            else:
                                logger.warning(f"Could not find ID in profile response: {item}")
                        except AttributeError as ae:
                            logger.warning(f"Database service doesn't have update_user_profile_sync_status method: {str(ae)}")
                        except Exception as e:
                            logger.error(f"Error updating profile sync status: {str(e)}")
                else:
                    failed_count += len(batch)
                    logger.error(f"Sync error: No response data")
                    
            except Exception as e:
                failed_count += len(batch)
                logger.error(f"Batch sync error: {str(e)}")
        
        # Update last sync status
        if synced_count > 0:
            self.last_sync["user_profiles"] = {
                "last_id": profiles[-1]["id"],
                "last_time": datetime.now().isoformat()
            }
            self._save_sync_state()
        
        logger.info(f"User profiles sync complete: {synced_count} synced, {failed_count} failed")
        
        return {
            "synced": synced_count,
            "failed": failed_count,
            "status": "complete" if failed_count == 0 else "partial"
        }
            
    except Exception as e:
        logger.error(f"User profiles sync error: {str(e)}")
        self.sync_failed = True
        self.sync_error = str(e)
        return {"synced": 0, "failed": len(profiles) if 'profiles' in locals() else 0, "status": "error"}
        
    finally:
        self.is_syncing = False
        
# New method: Sync time entries
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
        
        # Get last time entry sync ID
        last_sync_id = self.last_sync.get("time_entries", {}).get("last_id", '')
        
        # Get unsynchronized time entries
        try:
            time_entries = self.db_service.get_unsynchronized_time_entries(last_sync_id)
        except AttributeError:
            logger.warning("Database service doesn't have get_unsynchronized_time_entries method")
            self.is_syncing = False
            return {"synced": 0, "failed": 0, "status": "error"}
        
        if not time_entries:
            logger.info("No time entries to sync")
            self.is_syncing = False
            return {"synced": 0, "failed": 0, "status": "no_data"}
        
        logger.info(f"Syncing {len(time_entries)} time entries")
        
        # Prepare time entries for Supabase
        supabase_entries = []
        for entry in time_entries:
            # Build a valid Supabase record
            supabase_entry = {
                "id": entry["id"],
                "user_id": user_id,
                "org_id": org_id,
                "project_id": entry.get("project_id"),
                "task_id": entry.get("task_id"),
                "description": entry.get("description", ""),
                "start_time": entry["start_time"],
                "client_created_at": entry.get("created_at") or datetime.now().isoformat()
            }
            
            # Add optional fields only if they exist
            if entry.get("end_time"):
                supabase_entry["end_time"] = entry["end_time"]
            
            if entry.get("duration"):
                supabase_entry["duration"] = entry["duration"]
                
            if entry.get("is_active") is not None:
                supabase_entry["is_active"] = entry["is_active"]
                
            supabase_entries.append(supabase_entry)
        
        # Split into batches to avoid request size limits
        batch_size = 50
        batches = [supabase_entries[i:i + batch_size] for i in range(0, len(supabase_entries), batch_size)]
        
        synced_count = 0
        failed_count = 0
        
        for batch_index, batch in enumerate(batches):
            try:
                logger.info(f"Processing time entries batch {batch_index+1}/{len(batches)} ({len(batch)} items)")
                
                # Use Supabase client to insert data
                result = self.supabase.table("time_entries").upsert(batch).execute()
                
                if result and result.data:
                    batch_synced_count = len(result.data)
                    synced_count += batch_synced_count
                    logger.info(f"Successfully synced {batch_synced_count} time entries to Supabase")
                    
                    # Update local database with sync status
                    for i in range(batch_synced_count):
                        try:
                            # Get the original record that was sent
                            original_index = synced_count - batch_synced_count + i
                            if original_index < len(time_entries):
                                original_entry = time_entries[original_index]
                                entry_id = original_entry["id"]
                                
                                # Try to update sync status
                                try:
                                    logger.debug(f"Updating sync status for time entry: {entry_id}")
                                    self.db_service.update_time_entry_sync_status(entry_id, True)
                                except AttributeError:
                                    logger.warning("Database service doesn't have update_time_entry_sync_status method")
                                        
                        except Exception as update_error:
                            logger.error(f"Error updating time entry sync status: {str(update_error)}")
                else:
                    failed_count += len(batch)
                    logger.error(f"Sync error: No response data for batch {batch_index+1}")
                    
            except Exception as e:
                failed_count += len(batch)
                logger.error(f"Batch sync error for batch {batch_index+1}: {str(e)}")
        
        # Update last sync status
        if synced_count > 0:
            self.last_sync["time_entries"] = {
                "last_id": time_entries[-1]["id"],
                "last_time": datetime.now().isoformat()
            }
            self._save_sync_state()
        
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
        self.is_syncing = False

# New method: Sync user settings
async def sync_user_settings(self) -> Dict[str, Any]:
    """
    Synchronize user settings from local database to Supabase.
    
    Returns:
        dict: Sync results with counts and status
    """
    if not self.supabase:
        logger.error("Supabase client not initialized")
        return {"synced": 0, "failed": 0, "status": "error"}
        
    if not self.auth_service.is_authenticated():
        logger.warning("Cannot sync user settings: Not authenticated")
        return {"synced": 0, "failed": 0, "status": "not_authenticated"}
        
    try:
        # Only set is_syncing flag when called directly (not from sync_all)
        if not self.is_syncing:
            self.is_syncing = True
        self.sync_failed = False
        self.sync_error = None
        
        # Get user ID
        user_id = self.auth_service.user.get("id")
        
        # Get last setting sync ID
        last_sync_id = self.last_sync.get("user_settings", {}).get("last_id", '')
        
        # Get unsynchronized settings
        try:
            settings = self.db_service.get_unsynchronized_user_settings(last_sync_id)
        except AttributeError:
            logger.warning("Database service doesn't have get_unsynchronized_user_settings method")
            self.is_syncing = False
            return {"synced": 0, "failed": 0, "status": "error"}
        
        if not settings:
            logger.info("No user settings to sync")
            self.is_syncing = False
            return {"synced": 0, "failed": 0, "status": "no_data"}
        
        logger.info(f"Syncing {len(settings)} user settings")
        
        # Prepare settings for Supabase - mapping local fields to Supabase schema
        supabase_settings = []
        for setting in settings:
            # Only sync current user's settings using explicit user_id field or inferred from keys
            setting_user_id = setting.get("user_id") or user_id
            if setting_user_id == user_id:
                # Create normalized settings object with correct Supabase fields
                supabase_setting = {
                    "user_id": user_id,  # Use authenticated user's ID as primary key
                    "screenshot_interval": setting.get("screenshot_interval", 600),
                    "screenshot_quality": setting.get("screenshot_quality", "medium"),
                    "auto_sync_interval": setting.get("auto_sync_interval", 300),
                    "idle_detection_timeout": setting.get("idle_detection_timeout", 300),
                    "theme": setting.get("theme", "system"),
                    "notifications_enabled": setting.get("notifications_enabled", True),
                    "created_at": setting.get("created_at") or datetime.now().isoformat(),
                    "updated_at": setting.get("updated_at") or datetime.now().isoformat()
                }
                supabase_settings.append(supabase_setting)
        
        if not supabase_settings:
            logger.info("No user settings to sync for current user")
            self.is_syncing = False
            return {"synced": 0, "failed": 0, "status": "no_data"}
        
        # Split into batches to avoid request size limits
        batch_size = 20
        batches = [supabase_settings[i:i + batch_size] for i in range(0, len(supabase_settings), batch_size)]
        
        synced_count = 0
        failed_count = 0
        
        for batch in batches:
            try:
                # Use Supabase client to upsert data (insert or update)
                result = self.supabase.table("user_settings").upsert(batch).execute()
                
                if result and result.data:
                    # For user_settings, the primary key is user_id not id
                    synced_count += len(result.data)
                    logger.info(f"Successfully synced {len(result.data)} user settings to Supabase")
                    
                    # In user_settings, the setting is identified by user_id, not id
                    for item in result.data:
                        try:
                            # Try to get user_id from response, fallback to authenticated user's ID
                            setting_id = item.get("user_id", user_id)
                            if setting_id:
                                logger.info(f"Updating sync status for setting with user_id: {setting_id}")
                                self.db_service.update_user_setting_sync_status(setting_id, True)
                            else:
                                logger.warning(f"Could not determine user_id for setting: {item}")
                        except AttributeError as ae:
                            logger.warning(f"Database service doesn't have update_user_setting_sync_status method: {str(ae)}")
                        except Exception as e:
                            logger.error(f"Error updating setting sync status: {str(e)}")
                else:
                    failed_count += len(batch)
                    logger.error(f"Sync error: No response data")
                    
            except Exception as e:
                failed_count += len(batch)
                logger.error(f"Batch sync error: {str(e)}")
        
        # Update last sync status
        if synced_count > 0:
            self.last_sync["user_settings"] = {
                "last_id": settings[-1]["id"],
                "last_time": datetime.now().isoformat()
            }
            self._save_sync_state()
        
        logger.info(f"User settings sync complete: {synced_count} synced, {failed_count} failed")
        
        return {
            "synced": synced_count,
            "failed": failed_count,
            "status": "complete" if failed_count == 0 else "partial"
        }
            
    except Exception as e:
        logger.error(f"User settings sync error: {str(e)}")
        self.sync_failed = True
        self.sync_error = str(e)
        return {"synced": 0, "failed": len(settings) if 'settings' in locals() else 0, "status": "error"}
        
    finally:
        self.is_syncing = False

# Extend the sync_all method to include clients and projects
def extended_sync_all(original_method):
    """
    Extended version of sync_all that includes clients and projects.
    """
    async def wrapper(self, *args, **kwargs):
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
            clients_result = None
            projects_result = None
            tasks_result = None
            profiles_result = None 
            settings_result = None
            
            try:
                # Run the original sync_all method to handle organizations, activities, and screenshots
                original_result = await original_method(self, *args, **kwargs)
                
                # Extract results from original method
                org_result = original_result.get("organization")
                activity_result = original_result.get("activity_logs")
                screenshot_result = original_result.get("screenshots")
                
                # Add client sync
                logger.info("Starting clients sync")
                clients_start = datetime.now()
                clients_result = await self.sync_clients()
                clients_duration = (datetime.now() - clients_start).total_seconds()
                logger.info(f"Clients sync completed in {clients_duration:.2f}s with status: {clients_result.get('status', 'unknown')}")
                
                # Add project sync
                logger.info("Starting projects sync")
                projects_start = datetime.now()
                projects_result = await self.sync_projects()
                projects_duration = (datetime.now() - projects_start).total_seconds()
                logger.info(f"Projects sync completed in {projects_duration:.2f}s with status: {projects_result.get('status', 'unknown')}")
                
                # Add project tasks sync
                logger.info("Starting project tasks sync")
                tasks_start = datetime.now()
                try:
                    tasks_result = await self.sync_all_project_tasks()
                    tasks_duration = (datetime.now() - tasks_start).total_seconds()
                    logger.info(f"Project tasks sync completed in {tasks_duration:.2f}s with status: {tasks_result.get('status', 'unknown')}")
                except AttributeError:
                    logger.warning("sync_all_project_tasks method not found, skipping tasks sync")
                    tasks_result = {"status": "skipped", "message": "Method not available"}
                
                # Add user profiles sync
                logger.info("Starting user profiles sync")
                profiles_start = datetime.now()
                try:
                    profiles_result = await self.sync_user_profiles()
                    profiles_duration = (datetime.now() - profiles_start).total_seconds()
                    logger.info(f"User profiles sync completed in {profiles_duration:.2f}s with status: {profiles_result.get('status', 'unknown')}")
                except AttributeError:
                    logger.warning("sync_user_profiles method not found, skipping profiles sync")
                    profiles_result = {"status": "skipped", "message": "Method not available"}
                
                # Add user settings sync
                logger.info("Starting user settings sync")
                settings_start = datetime.now()
                try:
                    settings_result = await self.sync_user_settings()
                    settings_duration = (datetime.now() - settings_start).total_seconds()
                    logger.info(f"User settings sync completed in {settings_duration:.2f}s with status: {settings_result.get('status', 'unknown')}")
                except AttributeError:
                    logger.warning("sync_user_settings method not found, skipping settings sync")
                    settings_result = {"status": "skipped", "message": "Method not available"}
                
                # Add time entries sync
                logger.info("Starting time entries sync")
                time_entries_start = datetime.now()
                try:
                    time_entries_result = await self.sync_time_entries()
                    time_entries_duration = (datetime.now() - time_entries_start).total_seconds()
                    logger.info(f"Time entries sync completed in {time_entries_duration:.2f}s with status: {time_entries_result.get('status', 'unknown')}")
                except AttributeError:
                    logger.warning("sync_time_entries method not found, skipping time entries sync")
                    time_entries_result = {"status": "skipped", "message": "Method not available"}
                
                # Calculate overall duration
                total_duration = (datetime.now() - start_time).total_seconds()
                
                # Collect all results for analysis and logging
                all_results = {
                    "organization": org_result,
                    "activity_logs": activity_result, 
                    "screenshots": screenshot_result,
                    "clients": clients_result,
                    "projects": projects_result,
                    "project_tasks": tasks_result,
                    "user_profiles": profiles_result,
                    "user_settings": settings_result,
                    "time_entries": time_entries_result
                }
                
                # Log details of all component results
                for key, result in all_results.items():
                    if result:
                        status = result.get('status', 'unknown')
                        synced = result.get('synced', 0)
                        failed = result.get('failed', 0)
                        logger.debug(f"{key}: status={status}, synced={synced}, failed={failed}")
                
                # Determine overall status more intelligently
                valid_statuses = []
                
                # Process each result and add valid statuses to the list
                for key, result in all_results.items():
                    if not result:
                        continue
                    
                    status = result.get('status')
                    
                    # Skip 'no_data' and 'skipped' statuses for overall status determination
                    if status in ['no_data', 'skipped']:
                        continue
                        
                    valid_statuses.append(status)
                
                # If we have no valid statuses, everything was either skipped or no_data
                if not valid_statuses:
                    overall_status = "complete"
                # If any component had an error, overall status is error
                elif "error" in valid_statuses:
                    overall_status = "error"
                # If any component was partial, overall status is partial
                elif "partial" in valid_statuses:
                    overall_status = "partial"
                # Otherwise if all were complete, overall status is complete
                else:
                    overall_status = "complete"
                
                logger.info(f"Full sync completed in {total_duration:.2f}s with status: {overall_status}")
                
                return {
                    "organization": org_result,
                    "activity_logs": activity_result,
                    "screenshots": screenshot_result,
                    "clients": clients_result,
                    "projects": projects_result,
                    "project_tasks": tasks_result,
                    "user_profiles": profiles_result,
                    "user_settings": settings_result,
                    "time_entries": time_entries_result,
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
                    "clients": clients_result,
                    "projects": projects_result,
                    "project_tasks": tasks_result,
                    "user_profiles": profiles_result,
                    "user_settings": settings_result,
                    "time_entries": time_entries_result,
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
            
    return wrapper
