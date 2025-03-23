"""
Synchronization service for syncing local data with the server.
"""
import logging
import asyncio
import aiohttp
import os
import time
import json
from typing import Dict, Any, List, Optional, Tuple, Callable
from datetime import datetime, timedelta

from utils.config import Config
from services.database import DatabaseService
from services.auth import AuthService

# Setup logger
logger = logging.getLogger(__name__)

class SyncService:
    """
    Service for synchronizing local data with the server.
    
    Handles syncing activity logs, screenshots, and system metrics.
    """
    
    def __init__(
        self, 
        config: Optional[Config] = None,
        database: Optional[DatabaseService] = None,
        auth: Optional[AuthService] = None
    ):
        """
        Initialize the synchronization service.
        
        Args:
            config: Optional configuration object. If None, creates a new one.
            database: Optional database service. If None, creates a new one.
            auth: Optional authentication service. If None, creates a new one.
        """
        self.config = config or Config()
        self.database = database or DatabaseService(self.config)
        self.auth = auth or AuthService(self.config)
        
        # Get API URL from config
        self.api_url = self.config.get("api.url", "https://api.example.com")
        
        # Get sync settings
        self.sync_interval = self.config.get("tracking.sync_interval", 600)  # 10 minutes
        
        # Initialize state
        self.is_syncing = False
        self.sync_task = None
        self.active = False
        self.sync_callbacks = []
        
        # Lock for sync operations
        self.sync_lock = asyncio.Lock()
        
    async def start(self) -> bool:
        """
        Start the automatic sync process.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            if self.active:
                logger.warning("Sync service already running")
                return False
                
            logger.info(f"Starting sync service, sync interval: {self.sync_interval}s")
            self.active = True
            
            # Start the sync loop
            self.sync_task = asyncio.create_task(self._sync_loop())
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting sync service: {str(e)}")
            self.active = False
            return False
            
    async def stop(self) -> bool:
        """
        Stop the automatic sync process.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        try:
            if not self.active:
                logger.warning("Sync service not running")
                return False
                
            logger.info("Stopping sync service")
            self.active = False
            
            # Cancel the sync task if running
            if self.sync_task and not self.sync_task.done():
                self.sync_task.cancel()
                try:
                    await self.sync_task
                except asyncio.CancelledError:
                    pass
                    
            self.sync_task = None
            logger.info("Sync service stopped")
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping sync service: {str(e)}")
            self.active = False
            self.sync_task = None
            return False
            
    async def sync_all(self) -> Dict[str, Any]:
        """
        Synchronize all data types with the server.
        
        Returns:
            dict: Sync results
        """
        if not self.auth.is_authenticated():
            logger.warning("Cannot sync: not authenticated")
            return {
                "success": False,
                "error": "Not authenticated",
                "results": {}
            }
            
        # Prevent multiple sync operations running simultaneously
        async with self.sync_lock:
            if self.is_syncing:
                logger.warning("Sync already in progress")
                return {
                    "success": False,
                    "error": "Sync already in progress",
                    "results": {}
                }
                
            try:
                self.is_syncing = True
                start_time = time.time()
                
                logger.info("Starting sync operation")
                
                # Sync activity logs
                activity_result = await self._sync_activity_logs()
                
                # Sync screenshots
                screenshot_result = await self._sync_screenshots()
                
                # Sync system metrics
                metrics_result = await self._sync_system_metrics()
                
                # Compile results
                results = {
                    "activity_logs": activity_result,
                    "screenshots": screenshot_result,
                    "system_metrics": metrics_result,
                    "duration": time.time() - start_time
                }
                
                # Get sync counts
                synced_count = sum([
                    activity_result.get("synced", 0),
                    screenshot_result.get("synced", 0),
                    metrics_result.get("synced", 0)
                ])
                
                # Get errors
                has_errors = any([
                    activity_result.get("error"),
                    screenshot_result.get("error"),
                    metrics_result.get("error")
                ])
                
                if synced_count > 0:
                    logger.info(f"Sync completed, {synced_count} items synced")
                elif has_errors:
                    logger.warning("Sync completed with errors")
                else:
                    logger.info("Sync completed, no changes")
                    
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
                
            except Exception as e:
                logger.error(f"Error during sync: {str(e)}")
                return {
                    "success": False,
                    "error": str(e),
                    "results": {}
                }
                
            finally:
                self.is_syncing = False
                
    async def _sync_activity_logs(self) -> Dict[str, Any]:
        """
        Synchronize activity logs with the server.
        
        Returns:
            dict: Sync results
        """
        try:
            # Get sync status for activity logs
            sync_status = self.database.get_sync_status("activity_logs")
            last_synced_id = sync_status.get("last_synced_id", 0)
            
            # Get unsynced activity logs
            unsynced_logs = self.database.get_activity_logs(
                limit=50,  # Sync in batches to avoid memory issues
                synced=False
            )
            
            if not unsynced_logs:
                return {
                    "synced": 0,
                    "total": 0,
                    "last_id": last_synced_id
                }
                
            logger.info(f"Syncing {len(unsynced_logs)} activity logs")
            
            # Get access token
            access_token = await self.auth.get_access_token()
            if not access_token:
                return {
                    "error": "Not authenticated",
                    "synced": 0,
                    "total": len(unsynced_logs),
                    "last_id": last_synced_id
                }
                
            # Prepare sync request
            sync_url = f"{self.api_url}/api/v1/activity-logs/batch"
            
            # Format logs for API
            formatted_logs = [{
                "window_title": log.get("window_title", ""),
                "process_name": log.get("process_name", ""),
                "executable_path": log.get("executable_path", ""),
                "start_time": log.get("start_time", ""),
                "end_time": log.get("end_time"),
                "duration": log.get("duration", 0),
                "client_created_at": log.get("created_at", ""),
                "client_id": log.get("id", 0)
            } for log in unsynced_logs]
            
            # Send sync request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    sync_url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {access_token}"
                    },
                    json={
                        "logs": formatted_logs
                    }
                ) as response:
                    if response.status != 200:
                        error_body = await response.text()
                        logger.error(f"Activity log sync failed: {error_body}")
                        return {
                            "error": f"API error: {response.status}",
                            "synced": 0,
                            "total": len(unsynced_logs),
                            "last_id": last_synced_id
                        }
                        
                    # Parse response
                    result = await response.json()
                    
                    # Update sync status in database
                    synced_ids = result.get("synced_ids", [])
                    if synced_ids:
                        # Mark each synced log
                        for synced_id in synced_ids:
                            self.database.mark_synced("activity_logs", synced_id)
                            
                        # Update the last synced ID if greater
                        newest_synced_id = max(synced_ids)
                        if newest_synced_id > last_synced_id:
                            self.database.update_sync_status("activity_logs", newest_synced_id)
                            last_synced_id = newest_synced_id
                            
                    return {
                        "synced": len(synced_ids),
                        "total": len(unsynced_logs),
                        "last_id": last_synced_id
                    }
                    
        except Exception as e:
            logger.error(f"Error syncing activity logs: {str(e)}")
            return {
                "error": str(e),
                "synced": 0,
                "total": 0,
                "last_id": last_synced_id
            }
            
    async def _sync_screenshots(self) -> Dict[str, Any]:
        """
        Synchronize screenshots with the server.
        
        Returns:
            dict: Sync results
        """
        try:
            # Get sync status for screenshots
            sync_status = self.database.get_sync_status("screenshots")
            last_synced_id = sync_status.get("last_synced_id", 0)
            
            # Get unsynced screenshots
            unsynced_screenshots = self.database.get_screenshots(
                limit=10,  # Sync fewer screenshots at once due to file size
                synced=False
            )
            
            if not unsynced_screenshots:
                return {
                    "synced": 0,
                    "total": 0,
                    "last_id": last_synced_id
                }
                
            logger.info(f"Syncing {len(unsynced_screenshots)} screenshots")
            
            # Get access token
            access_token = await self.auth.get_access_token()
            if not access_token:
                return {
                    "error": "Not authenticated",
                    "synced": 0,
                    "total": len(unsynced_screenshots),
                    "last_id": last_synced_id
                }
                
            # Sync each screenshot individually
            synced_count = 0
            synced_ids = []
            
            for screenshot in unsynced_screenshots:
                # Check if file exists
                filepath = screenshot.get("filepath")
                if not os.path.exists(filepath):
                    logger.warning(f"Screenshot file not found: {filepath}")
                    continue
                    
                # Upload screenshot
                upload_result = await self._upload_screenshot(
                    screenshot_id=screenshot.get("id"),
                    filepath=filepath,
                    timestamp=screenshot.get("timestamp"),
                    activity_log_id=screenshot.get("activity_log_id"),
                    access_token=access_token
                )
                
                if upload_result.get("success"):
                    synced_count += 1
                    synced_ids.append(screenshot.get("id"))
                    
            # Update sync status
            if synced_ids:
                # Mark each synced screenshot
                for synced_id in synced_ids:
                    self.database.mark_synced("screenshots", synced_id)
                    
                # Update the last synced ID if greater
                newest_synced_id = max(synced_ids)
                if newest_synced_id > last_synced_id:
                    self.database.update_sync_status("screenshots", newest_synced_id)
                    last_synced_id = newest_synced_id
                    
            return {
                "synced": synced_count,
                "total": len(unsynced_screenshots),
                "last_id": last_synced_id
            }
            
        except Exception as e:
            logger.error(f"Error syncing screenshots: {str(e)}")
            return {
                "error": str(e),
                "synced": 0,
                "total": 0,
                "last_id": last_synced_id
            }
            
    async def _upload_screenshot(
        self,
        screenshot_id: int,
        filepath: str,
        timestamp: str,
        activity_log_id: Optional[int] = None,
        access_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload a screenshot to the server.
        
        Args:
            screenshot_id: Screenshot ID
            filepath: Path to the screenshot file
            timestamp: Screenshot timestamp
            activity_log_id: Related activity log ID (optional)
            access_token: Access token (optional)
            
        Returns:
            dict: Upload result
        """
        try:
            # Get access token if not provided
            if not access_token:
                access_token = await self.auth.get_access_token()
                if not access_token:
                    return {
                        "success": False,
                        "error": "Not authenticated"
                    }
                    
            # Prepare upload request
            upload_url = f"{self.api_url}/api/v1/screenshots"
            
            # Create form data with file
            async with aiohttp.ClientSession() as session:
                with open(filepath, 'rb') as f:
                    form_data = aiohttp.FormData()
                    form_data.add_field(
                        'file',
                        f,
                        filename=os.path.basename(filepath),
                        content_type='image/png'
                    )
                    form_data.add_field('timestamp', timestamp)
                    form_data.add_field('client_id', str(screenshot_id))
                    
                    if activity_log_id:
                        form_data.add_field('activity_log_id', str(activity_log_id))
                        
                    # Send upload request
                    async with session.post(
                        upload_url,
                        headers={
                            "Authorization": f"Bearer {access_token}"
                        },
                        data=form_data
                    ) as response:
                        if response.status != 200:
                            error_body = await response.text()
                            logger.error(f"Screenshot upload failed: {error_body}")
                            return {
                                "success": False,
                                "error": f"API error: {response.status}"
                            }
                            
                        # Parse response
                        result = await response.json()
                        
                        return {
                            "success": True,
                            "result": result
                        }
                        
        except Exception as e:
            logger.error(f"Error uploading screenshot {screenshot_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def _sync_system_metrics(self) -> Dict[str, Any]:
        """
        Synchronize system metrics with the server.
        
        Returns:
            dict: Sync results
        """
        try:
            # Get sync status for system metrics
            sync_status = self.database.get_sync_status("system_metrics")
            last_synced_id = sync_status.get("last_synced_id", 0)
            
            # Get unsynced metrics
            unsynced_metrics = self.database.get_system_metrics(
                limit=100,  # Metrics are small, so we can sync more at once
                synced=False
            )
            
            if not unsynced_metrics:
                return {
                    "synced": 0,
                    "total": 0,
                    "last_id": last_synced_id
                }
                
            logger.info(f"Syncing {len(unsynced_metrics)} system metrics")
            
            # Get access token
            access_token = await self.auth.get_access_token()
            if not access_token:
                return {
                    "error": "Not authenticated",
                    "synced": 0,
                    "total": len(unsynced_metrics),
                    "last_id": last_synced_id
                }
                
            # Prepare sync request
            sync_url = f"{self.api_url}/api/v1/system-metrics/batch"
            
            # Format metrics for API
            formatted_metrics = [{
                "cpu_percent": metric.get("cpu_percent", 0),
                "memory_percent": metric.get("memory_percent", 0),
                "battery_percent": metric.get("battery_percent"),
                "battery_charging": metric.get("battery_charging"),
                "timestamp": metric.get("timestamp", ""),
                "activity_log_id": metric.get("activity_log_id"),
                "client_created_at": metric.get("created_at", ""),
                "client_id": metric.get("id", 0)
            } for metric in unsynced_metrics]
            
            # Send sync request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    sync_url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {access_token}"
                    },
                    json={
                        "metrics": formatted_metrics
                    }
                ) as response:
                    if response.status != 200:
                        error_body = await response.text()
                        logger.error(f"System metrics sync failed: {error_body}")
                        return {
                            "error": f"API error: {response.status}",
                            "synced": 0,
                            "total": len(unsynced_metrics),
                            "last_id": last_synced_id
                        }
                        
                    # Parse response
                    result = await response.json()
                    
                    # Update sync status in database
                    synced_ids = result.get("synced_ids", [])
                    if synced_ids:
                        # Mark each synced metric
                        for synced_id in synced_ids:
                            self.database.mark_synced("system_metrics", synced_id)
                            
                        # Update the last synced ID if greater
                        newest_synced_id = max(synced_ids)
                        if newest_synced_id > last_synced_id:
                            self.database.update_sync_status("system_metrics", newest_synced_id)
                            last_synced_id = newest_synced_id
                            
                    return {
                        "synced": len(synced_ids),
                        "total": len(unsynced_metrics),
                        "last_id": last_synced_id
                    }
                    
        except Exception as e:
            logger.error(f"Error syncing system metrics: {str(e)}")
            return {
                "error": str(e),
                "synced": 0,
                "total": 0,
                "last_id": last_synced_id
            }
            
    async def _sync_loop(self) -> None:
        """
        Main sync loop that runs in a separate task.
        
        Periodically synchronizes data with the server.
        """
        logger.info(f"Sync loop started, interval: {self.sync_interval}s")
        
        while self.active:
            try:
                # Check if authenticated
                if self.auth.is_authenticated():
                    # Perform sync
                    await self.sync_all()
                else:
                    logger.debug("Skipping sync: not authenticated")
                    
            except Exception as e:
                logger.error(f"Error in sync loop: {str(e)}")
                
            # Sleep for the configured interval
            try:
                # Use asyncio.sleep to allow cancellation
                await asyncio.sleep(self.sync_interval)
            except asyncio.CancelledError:
                logger.info("Sync loop cancelled")
                break
                
        logger.info("Sync loop stopped")
        
    def get_sync_status(self) -> Dict[str, Any]:
        """
        Get current sync status.
        
        Returns:
            dict: Sync status
        """
        try:
            # Get sync status for each entity type
            activity_status = self.database.get_sync_status("activity_logs")
            screenshot_status = self.database.get_sync_status("screenshots")
            metrics_status = self.database.get_sync_status("system_metrics")
            
            # Get database statistics
            stats = self.database.get_statistics()
            
            return {
                "is_syncing": self.is_syncing,
                "active": self.active,
                "last_sync": {
                    "activity_logs": activity_status.get("last_sync_time"),
                    "screenshots": screenshot_status.get("last_sync_time"),
                    "system_metrics": metrics_status.get("last_sync_time")
                },
                "unsynced_counts": {
                    "activity_logs": stats.get("activity_logs_unsynced", 0),
                    "screenshots": stats.get("screenshots_unsynced", 0),
                    "system_metrics": stats.get("system_metrics_unsynced", 0)
                },
                "authenticated": self.auth.is_authenticated()
            }
            
        except Exception as e:
            logger.error(f"Error getting sync status: {str(e)}")
            return {
                "is_syncing": self.is_syncing,
                "active": self.active,
                "error": str(e)
            }
            
    def add_sync_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Add a callback to be called when synchronization completes.
        
        Args:
            callback: Callback function that takes a result dictionary
        """
        if callback not in self.sync_callbacks:
            self.sync_callbacks.append(callback)
            
    def remove_sync_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Remove a sync callback.
        
        Args:
            callback: Callback function to remove
        """
        if callback in self.sync_callbacks:
            self.sync_callbacks.remove(callback)
