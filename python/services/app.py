"""
Main application service for the Time Tracker desktop application.
"""
import logging
import os
import asyncio
from typing import Dict, Any, Optional, List, Callable

from utils.config import Config
from services.auth import AuthService
from services.database import DatabaseService
from services.activity import ActivityTrackingService
from services.screenshots import ScreenshotManagementService
from services.sync import SyncService

# Setup logger
logger = logging.getLogger(__name__)

class AppService:
    """
    Main application service that manages all other services.
    
    Acts as the central coordinator for the Time Tracker desktop application.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the application service with all required services.
        
        Args:
            config_path: Optional custom path to the config file.
                         If None, uses the default path.
        """
        # Initialize config first (singleton)
        self.config = Config(config_path)
        
        # Initialize database service
        self.database = DatabaseService(self.config)
        
        # Initialize authentication service
        self.auth = AuthService(self.config)
        
        # Initialize activity tracking service
        self.activity = ActivityTrackingService(self.config, self.database)
        
        # Initialize screenshot service with activity tracking
        self.screenshots = ScreenshotManagementService(
            self.config, 
            self.database,
            self.activity
        )
        
        # Initialize sync service
        self.sync = SyncService(self.config, self.database, self.auth)
        
        # Application state
        self.is_tracking = False
        self.is_running = False
        self.app_callbacks = []
        
    async def start_app(self) -> bool:
        """
        Start the application and initialize all services.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            if self.is_running:
                logger.warning("Application already running")
                return False
                
            logger.info("Starting Time Tracker application")
            
            # Set app as running
            self.is_running = True
            
            # Start sync service
            await self.sync.start()
            
            # Auto-start tracking if configured
            if self.config.get("tracking.auto_start", False):
                await self.start_tracking()
                
            logger.info("Time Tracker application started successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting application: {str(e)}")
            self.is_running = False
            return False
            
    async def stop_app(self) -> bool:
        """
        Stop the application and all services.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        try:
            if not self.is_running:
                logger.warning("Application already stopped")
                return False
                
            logger.info("Stopping Time Tracker application")
            
            # Stop tracking if active
            if self.is_tracking:
                await self.stop_tracking()
                
            # Stop sync service
            await self.sync.stop()
            
            # Close database connection
            self.database.close()
            
            # Set app as stopped
            self.is_running = False
            
            logger.info("Time Tracker application stopped successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping application: {str(e)}")
            self.is_running = False
            return False
            
    async def start_tracking(self) -> bool:
        """
        Start activity tracking and screenshot capturing.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        try:
            if self.is_tracking:
                logger.warning("Tracking already active")
                return False
                
            # Start activity tracking
            activity_success = self.activity.start()
            if not activity_success:
                logger.error("Failed to start activity tracking")
                return False
                
            # Start screenshot service
            if self.config.get("tracking.capture_screenshots", True):
                screenshot_success = self.screenshots.start()
                if not screenshot_success:
                    logger.warning("Failed to start screenshot service")
                    # Continue anyway, as screenshots are optional
            
            self.is_tracking = True
            logger.info("Tracking started")
            
            # Notify callbacks
            await self._notify_app_callbacks({
                "event": "tracking_started",
                "timestamp": await self._get_timestamp()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting tracking: {str(e)}")
            # Try to stop any started services
            self.activity.stop()
            self.screenshots.stop()
            self.is_tracking = False
            return False
            
    async def stop_tracking(self) -> bool:
        """
        Stop activity tracking and screenshot capturing.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        try:
            if not self.is_tracking:
                logger.warning("Tracking not active")
                return False
                
            # Stop screenshot service
            if self.screenshots.active:
                screenshot_success = self.screenshots.stop()
                if not screenshot_success:
                    logger.warning("Failed to stop screenshot service")
                    # Continue anyway
            
            # Stop activity tracking
            activity_success = self.activity.stop()
            if not activity_success:
                logger.error("Failed to stop activity tracking")
                return False
                
            self.is_tracking = False
            logger.info("Tracking stopped")
            
            # Notify callbacks
            await self._notify_app_callbacks({
                "event": "tracking_stopped",
                "timestamp": await self._get_timestamp()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error stopping tracking: {str(e)}")
            self.is_tracking = False
            return False
            
    async def pause_tracking(self) -> bool:
        """
        Pause activity tracking temporarily.
        
        Returns:
            bool: True if paused successfully, False otherwise
        """
        try:
            if not self.is_tracking:
                logger.warning("Tracking not active")
                return False
                
            # Just pause activity tracking, keep screenshots running
            activity_success = self.activity.pause()
            if not activity_success:
                logger.error("Failed to pause activity tracking")
                return False
                
            logger.info("Tracking paused")
            
            # Notify callbacks
            await self._notify_app_callbacks({
                "event": "tracking_paused",
                "timestamp": await self._get_timestamp()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error pausing tracking: {str(e)}")
            return False
            
    async def resume_tracking(self) -> bool:
        """
        Resume activity tracking after being paused.
        
        Returns:
            bool: True if resumed successfully, False otherwise
        """
        try:
            if not self.is_tracking:
                logger.warning("Tracking not active, start it first")
                return False
                
            # Resume activity tracking
            activity_success = self.activity.resume()
            if not activity_success:
                logger.error("Failed to resume activity tracking")
                return False
                
            logger.info("Tracking resumed")
            
            # Notify callbacks
            await self._notify_app_callbacks({
                "event": "tracking_resumed",
                "timestamp": await self._get_timestamp()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error resuming tracking: {str(e)}")
            return False
            
    async def capture_screenshot(self) -> Optional[Dict[str, Any]]:
        """
        Capture a screenshot immediately.
        
        Returns:
            dict: Screenshot metadata or None if failed
        """
        try:
            if not self.is_tracking:
                logger.warning("Tracking not active, screenshots may not be linked to activities")
                
            # Capture screenshot
            screenshot = await self.screenshots.capture_screenshot()
            if not screenshot:
                logger.error("Failed to capture screenshot")
                return None
                
            logger.info(f"Screenshot captured: {screenshot['id']}")
            
            # Notify callbacks
            await self._notify_app_callbacks({
                "event": "screenshot_captured",
                "screenshot_id": screenshot['id'],
                "timestamp": await self._get_timestamp()
            })
            
            return screenshot
            
        except Exception as e:
            logger.error(f"Error capturing screenshot: {str(e)}")
            return None
            
    async def sync_data(self) -> Dict[str, Any]:
        """
        Synchronize local data with the server.
        
        Returns:
            dict: Sync results
        """
        try:
            logger.info("Starting manual data synchronization")
            
            # Check if authenticated
            if not self.auth.is_authenticated():
                logger.warning("Not authenticated, cannot sync data")
                return {
                    "success": False,
                    "error": "Not authenticated"
                }
                
            # Perform sync
            results = await self.sync.sync_all()
            
            # Notify callbacks
            await self._notify_app_callbacks({
                "event": "data_synced",
                "results": results,
                "timestamp": await self._get_timestamp()
            })
            
            return results
            
        except Exception as e:
            logger.error(f"Error syncing data: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Log in the user.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            dict: User information
        """
        try:
            user = await self.auth.login(email, password)
            
            # Notify callbacks
            await self._notify_app_callbacks({
                "event": "user_logged_in",
                "user": user,
                "timestamp": await self._get_timestamp()
            })
            
            return user
            
        except Exception as e:
            logger.error(f"Error logging in: {str(e)}")
            raise
            
    async def logout(self) -> bool:
        """
        Log out the user.
        
        Returns:
            bool: True if logged out successfully
        """
        try:
            # Stop tracking if active
            if self.is_tracking:
                await self.stop_tracking()
                
            # Log out
            success = await self.auth.logout()
            
            if success:
                # Notify callbacks
                await self._notify_app_callbacks({
                    "event": "user_logged_out",
                    "timestamp": await self._get_timestamp()
                })
                
            return success
            
        except Exception as e:
            logger.error(f"Error logging out: {str(e)}")
            return False
            
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current application status.
        
        Returns:
            dict: Application status
        """
        return {
            "is_running": self.is_running,
            "is_tracking": self.is_tracking,
            "is_authenticated": self.auth.is_authenticated(),
            "user": self.auth.get_user(),
            "activity": self.activity.get_status() if self.activity else None,
            "sync": self.sync.get_sync_status() if self.sync else None
        }
        
    def get_recent_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent activity logs.
        
        Args:
            limit: Maximum number of activities to return
            
        Returns:
            list: Recent activity logs
        """
        return self.activity.get_recent_activities(limit)
        
    def get_recent_screenshots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent screenshots.
        
        Args:
            limit: Maximum number of screenshots to return
            
        Returns:
            list: Recent screenshots
        """
        return self.screenshots.get_recent_screenshots(limit)
        
    def add_app_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Add a callback to be called on application events.
        
        Args:
            callback: Callback function that takes an event dictionary
        """
        if callback not in self.app_callbacks:
            self.app_callbacks.append(callback)
            
    def remove_app_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Remove an application callback.
        
        Args:
            callback: Callback function to remove
        """
        if callback in self.app_callbacks:
            self.app_callbacks.remove(callback)
            
    async def _notify_app_callbacks(self, event: Dict[str, Any]) -> None:
        """
        Notify all registered callbacks about an application event.
        
        Args:
            event: Event dictionary
        """
        for callback in self.app_callbacks:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Error in app callback: {str(e)}")
                
    async def _get_timestamp(self) -> str:
        """
        Get the current timestamp in ISO format.
        
        Returns:
            str: Current timestamp
        """
        from datetime import datetime
        return datetime.utcnow().isoformat()
