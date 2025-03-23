"""
Extension methods for the SyncService class to handle clients, projects, and settings.
"""
import logging
import aiohttp
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
# Setup logger
logger = logging.getLogger(__name__)

# Clients sync method
async def _sync_clients(self) -> Dict[str, Any]:
    """
    Synchronize clients with the server.
    
    Returns:
        dict: Sync results
    """
    try:
        # Initialize results
        sync_status = self.database.get_sync_status("clients")
        last_synced_id = sync_status.get("last_synced_id", 0)
        
        # Get unsynced clients
        unsynced_clients = self.database.get_clients(
            limit=50,
            synced=False
        )
        
        if not unsynced_clients:
            return {
                "synced": 0,
                "total": 0,
                "last_id": last_synced_id
            }
        
        logger.info(f"Syncing {len(unsynced_clients)} clients")
        
        # Get access token
        access_token = await self.auth.get_access_token()
        if not access_token:
            return {
                "error": "Not authenticated",
                "synced": 0,
                "total": len(unsynced_clients),
                "last_id": last_synced_id
            }
        
        # Prepare sync request
        sync_url = f"{self.api_url}/api/v1/clients/batch"
        
        # Format clients for API
        formatted_clients = [{
            "id": client.get("id"),
            "name": client.get("name", ""),
            "contact_name": client.get("contact_name"),
            "email": client.get("email"),
            "phone": client.get("phone"),
            "address": client.get("address"),
            "notes": client.get("notes"),
            "is_active": client.get("is_active", True),
            "client_created_at": client.get("created_at"),
            "client_updated_at": client.get("updated_at")
        } for client in unsynced_clients]
        
        # Send sync request
        async with aiohttp.ClientSession() as session:
            async with session.post(
                sync_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"
                },
                json={
                    "clients": formatted_clients
                }
            ) as response:
                if response.status != 200:
                    error_body = await response.text()
                    logger.error(f"Client sync failed: {error_body}")
                    return {
                        "error": f"API error: {response.status}",
                        "synced": 0,
                        "total": len(unsynced_clients),
                        "last_id": last_synced_id
                    }
                
                # Parse response
                result = await response.json()
                
                # Update sync status in database
                synced_ids = result.get("synced_ids", [])
                if synced_ids:
                    # Mark each synced client
                    for synced_id in synced_ids:
                        self.database.mark_synced("clients", synced_id)
                
                return {
                    "synced": len(synced_ids),
                    "total": len(unsynced_clients),
                    "last_id": last_synced_id
                }
    
    except Exception as e:
        logger.error(f"Error syncing clients: {str(e)}")
        return {
            "error": str(e),
            "synced": 0,
            "total": 0,
            "last_id": last_synced_id
        }

# Projects sync method
async def _sync_projects(self) -> Dict[str, Any]:
    """
    Synchronize projects with the server.
    
    Returns:
        dict: Sync results
    """
    try:
        # Initialize results
        sync_status = self.database.get_sync_status("projects")
        last_synced_id = sync_status.get("last_synced_id", 0)
        
        # Get unsynced projects
        unsynced_projects = self.database.get_projects(
            limit=50,
            synced=False
        )
        
        if not unsynced_projects:
            return {
                "synced": 0,
                "total": 0,
                "last_id": last_synced_id
            }
        
        logger.info(f"Syncing {len(unsynced_projects)} projects")
        
        # Get access token
        access_token = await self.auth.get_access_token()
        if not access_token:
            return {
                "error": "Not authenticated",
                "synced": 0,
                "total": len(unsynced_projects),
                "last_id": last_synced_id
            }
        
        # Prepare sync request
        sync_url = f"{self.api_url}/api/v1/projects/batch"
        
        # Format projects for API
        formatted_projects = [{
            "id": project.get("id"),
            "name": project.get("name", ""),
            "description": project.get("description"),
            "client_id": project.get("client_id"),
            "color": project.get("color"),
            "hourly_rate": project.get("hourly_rate"),
            "is_billable": project.get("is_billable", True),
            "is_active": project.get("is_active", True),
            "client_created_at": project.get("created_at"),
            "client_updated_at": project.get("updated_at")
        } for project in unsynced_projects]
        
        # Send sync request
        async with aiohttp.ClientSession() as session:
            async with session.post(
                sync_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"
                },
                json={
                    "projects": formatted_projects
                }
            ) as response:
                if response.status != 200:
                    error_body = await response.text()
                    logger.error(f"Project sync failed: {error_body}")
                    return {
                        "error": f"API error: {response.status}",
                        "synced": 0,
                        "total": len(unsynced_projects),
                        "last_id": last_synced_id
                    }
                
                # Parse response
                result = await response.json()
                
                # Update sync status in database
                synced_ids = result.get("synced_ids", [])
                if synced_ids:
                    # Mark each synced project
                    for synced_id in synced_ids:
                        self.database.mark_synced("projects", synced_id)
                
                return {
                    "synced": len(synced_ids),
                    "total": len(unsynced_projects),
                    "last_id": last_synced_id
                }
    
    except Exception as e:
        logger.error(f"Error syncing projects: {str(e)}")
        return {
            "error": str(e),
            "synced": 0,
            "total": 0,
            "last_id": last_synced_id
        }

# Project Tasks sync method
async def _sync_project_tasks(self) -> Dict[str, Any]:
    """
    Synchronize project tasks with the server.
    
    Returns:
        dict: Sync results
    """
    try:
        # Initialize results
        sync_status = self.database.get_sync_status("project_tasks")
        last_synced_id = sync_status.get("last_synced_id", 0)
        
        # Get unsynced tasks for all projects
        unsynced_tasks = []
        
        # Get all projects
        projects = self.database.get_projects(limit=100)
        
        for project in projects:
            tasks = self.database.get_project_tasks(
                project_id=project.get("id"),
                limit=20,
                synced=False
            )
            unsynced_tasks.extend(tasks)
        
        if not unsynced_tasks:
            return {
                "synced": 0,
                "total": 0,
                "last_id": last_synced_id
            }
        
        logger.info(f"Syncing {len(unsynced_tasks)} project tasks")
        
        # Get access token
        access_token = await self.auth.get_access_token()
        if not access_token:
            return {
                "error": "Not authenticated",
                "synced": 0,
                "total": len(unsynced_tasks),
                "last_id": last_synced_id
            }
        
        # Prepare sync request
        sync_url = f"{self.api_url}/api/v1/project-tasks/batch"
        
        # Format tasks for API
        formatted_tasks = [{
            "id": task.get("id"),
            "name": task.get("name", ""),
            "description": task.get("description"),
            "project_id": task.get("project_id"),
            "estimated_hours": task.get("estimated_hours"),
            "is_active": task.get("is_active", True),
            "client_created_at": task.get("created_at"),
            "client_updated_at": task.get("updated_at")
        } for task in unsynced_tasks]
        
        # Send sync request
        async with aiohttp.ClientSession() as session:
            async with session.post(
                sync_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"
                },
                json={
                    "tasks": formatted_tasks
                }
            ) as response:
                if response.status != 200:
                    error_body = await response.text()
                    logger.error(f"Project task sync failed: {error_body}")
                    return {
                        "error": f"API error: {response.status}",
                        "synced": 0,
                        "total": len(unsynced_tasks),
                        "last_id": last_synced_id
                    }
                
                # Parse response
                result = await response.json()
                
                # Update sync status in database
                synced_ids = result.get("synced_ids", [])
                if synced_ids:
                    # Mark each synced task
                    for synced_id in synced_ids:
                        self.database.mark_synced("project_tasks", synced_id)
                
                return {
                    "synced": len(synced_ids),
                    "total": len(unsynced_tasks),
                    "last_id": last_synced_id
                }
    
    except Exception as e:
        logger.error(f"Error syncing project tasks: {str(e)}")
        return {
            "error": str(e),
            "synced": 0,
            "total": 0,
            "last_id": last_synced_id
        }

# User Settings sync method
async def _sync_user_settings(self) -> Dict[str, Any]:
    """
    Synchronize user settings with the server.
    
    Returns:
        dict: Sync results
    """
    try:
        # Get access token
        access_token = await self.auth.get_access_token()
        if not access_token:
            return {
                "error": "Not authenticated",
                "synced": 0,
                "total": 0
            }
        
        # Get user ID from access token
        user = self.auth.get_user()
        user_id = user.get("id")
        if not user_id:
            return {
                "error": "User ID not available",
                "synced": 0,
                "total": 0
            }
        
        # Get user settings
        settings = self.database.get_user_settings(user_id)
        
        if not settings or settings.get("synced"):
            return {
                "synced": 0,
                "total": 0
            }
        
        logger.info(f"Syncing user settings")
        
        # Prepare sync request
        sync_url = f"{self.api_url}/api/v1/user-settings"
        
        # Format settings for API
        formatted_settings = {
            "screenshot_interval": settings.get("screenshot_interval"),
            "screenshot_quality": settings.get("screenshot_quality"),
            "auto_sync_interval": settings.get("auto_sync_interval"),
            "idle_detection_timeout": settings.get("idle_detection_timeout"),
            "theme": settings.get("theme"),
            "notifications_enabled": settings.get("notifications_enabled")
        }
        
        # Send sync request
        async with aiohttp.ClientSession() as session:
            async with session.put(
                sync_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"
                },
                json=formatted_settings
            ) as response:
                if response.status not in (200, 201):
                    error_body = await response.text()
                    logger.error(f"User settings sync failed: {error_body}")
                    return {
                        "error": f"API error: {response.status}",
                        "synced": 0,
                        "total": 1
                    }
                
                # Mark settings as synced
                self.database.mark_synced("user_settings", user_id)
                
                return {
                    "synced": 1,
                    "total": 1
                }
    
    except Exception as e:
        logger.error(f"Error syncing user settings: {str(e)}")
        return {
            "error": str(e),
            "synced": 0,
            "total": 0
        }

# User Profile sync method
async def _sync_user_profile(self) -> Dict[str, Any]:
    """
    Synchronize user profile with the server.
    
    Returns:
        dict: Sync results
    """
    try:
        # Get access token
        access_token = await self.auth.get_access_token()
        if not access_token:
            return {
                "error": "Not authenticated",
                "synced": 0,
                "total": 0
            }
        
        # Get user ID from access token
        user = self.auth.get_user()
        user_id = user.get("id")
        if not user_id:
            return {
                "error": "User ID not available",
                "synced": 0,
                "total": 0
            }
        
        # Get user profile
        profile = self.database.get_user_profile(user_id)
        
        if not profile or profile.get("synced"):
            return {
                "synced": 0,
                "total": 0
            }
        
        logger.info(f"Syncing user profile")
        
        # Prepare sync request
        sync_url = f"{self.api_url}/api/v1/user-profile"
        
        # Format profile for API
        formatted_profile = {
            "name": profile.get("name"),
            "email": profile.get("email"),
            "timezone": profile.get("timezone"),
            "hourly_rate": profile.get("hourly_rate"),
            "avatar_url": profile.get("avatar_url")
        }
        
        # Send sync request
        async with aiohttp.ClientSession() as session:
            async with session.put(
                sync_url,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {access_token}"
                },
                json=formatted_profile
            ) as response:
                if response.status not in (200, 201):
                    error_body = await response.text()
                    logger.error(f"User profile sync failed: {error_body}")
                    return {
                        "error": f"API error: {response.status}",
                        "synced": 0,
                        "total": 1
                    }
                
                # Mark profile as synced
                self.database.mark_synced("user_profiles", user_id)
                
                return {
                    "synced": 1,
                    "total": 1
                }
    
    except Exception as e:
        logger.error(f"Error syncing user profile: {str(e)}")
        return {
            "error": str(e),
            "synced": 0,
            "total": 0
        }

# Extend the sync_all method
async def sync_all_extended(self) -> Dict[str, Any]:
    """
    Extended version of sync_all that also syncs clients, projects, and user data.
    
    This wrapper calls the original sync_all method first, then adds the new entities.
    
    Returns:
        dict: Sync results
    """
    # Call the original sync_all method
    original_result = await self._original_sync_all()
    
    # If the original sync failed, return the error
    if not original_result.get("success", False):
        return original_result
    
    # Extract the results from the original sync
    results = original_result.get("results", {})
    
    # Sync new entities
    client_result = await self._sync_clients()
    project_result = await self._sync_projects()
    task_result = await self._sync_project_tasks()
    settings_result = await self._sync_user_settings()
    profile_result = await self._sync_user_profile()
    
    # Add new results
    results.update({
        "clients": client_result,
        "projects": project_result,
        "project_tasks": task_result,
        "user_settings": settings_result,
        "user_profile": profile_result
    })
    
    # Get sync counts
    synced_count = sum([
        results.get("activity_logs", {}).get("synced", 0),
        results.get("screenshots", {}).get("synced", 0),
        results.get("system_metrics", {}).get("synced", 0),
        client_result.get("synced", 0),
        project_result.get("synced", 0),
        task_result.get("synced", 0),
        settings_result.get("synced", 0),
        profile_result.get("synced", 0)
    ])
    
    # Get errors
    has_errors = any([
        results.get("activity_logs", {}).get("error"),
        results.get("screenshots", {}).get("error"),
        results.get("system_metrics", {}).get("error"),
        client_result.get("error"),
        project_result.get("error"),
        task_result.get("error"),
        settings_result.get("error"),
        profile_result.get("error")
    ])
    
    if synced_count > 0:
        logger.info(f"Extended sync completed, {synced_count} items synced")
    elif has_errors:
        logger.warning("Extended sync completed with errors")
    else:
        logger.info("Extended sync completed, no changes")
    
    # Notify callbacks
    for callback in self.sync_callbacks:
        try:
            callback(results)
        except Exception as e:
            logger.error(f"Error in sync callback: {str(e)}")
    
    return {
        "success": True,
        "results": results
    }

# Extend the get_sync_status method
def get_sync_status_extended(self) -> Dict[str, Any]:
    """
    Extended version of get_sync_status that includes new entities.
    
    Returns:
        dict: Extended sync status
    """
    # Get the original status
    original_status = self._original_get_sync_status()
    
    try:
        # Get sync status for new entity types
        clients_status = self.database.get_sync_status("clients")
        projects_status = self.database.get_sync_status("projects")
        tasks_status = self.database.get_sync_status("project_tasks")
        
        # Get counts of unsynced entities
        unsynced_clients = len(self.database.get_clients(synced=False))
        unsynced_projects = len(self.database.get_projects(synced=False))
        
        # Get unsynced tasks count
        unsynced_tasks = 0
        projects = self.database.get_projects(limit=100)
        for project in projects:
            unsynced_tasks += len(self.database.get_project_tasks(
                project_id=project.get("id"),
                synced=False
            ))
        
        # Add user settings and profile status
        user = self.auth.get_user()
        user_id = user.get("id")
        unsynced_settings = 0
        unsynced_profile = 0
        if user_id:
            settings = self.database.get_user_settings(user_id)
            profile = self.database.get_user_profile(user_id)
            unsynced_settings = 0 if settings.get("synced") else 1
            unsynced_profile = 0 if profile.get("synced") else 1
        
        # Update the last_sync object
        if "last_sync" in original_status:
            original_status["last_sync"].update({
                "clients": clients_status.get("last_sync_time"),
                "projects": projects_status.get("last_sync_time"),
                "project_tasks": tasks_status.get("last_sync_time"),
                "user_settings": datetime.now().isoformat() if unsynced_settings == 0 else None,
                "user_profile": datetime.now().isoformat() if unsynced_profile == 0 else None
            })
        
        # Update the unsynced_counts object
        if "unsynced_counts" in original_status:
            original_status["unsynced_counts"].update({
                "clients": unsynced_clients,
                "projects": unsynced_projects,
                "project_tasks": unsynced_tasks,
                "user_settings": unsynced_settings,
                "user_profile": unsynced_profile
            })
        
        return original_status
        
    except Exception as e:
        logger.error(f"Error getting extended sync status: {str(e)}")
        return original_status
