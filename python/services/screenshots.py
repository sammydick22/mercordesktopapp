"""
Screenshot management service for capturing and storing screenshots.
"""
import logging
import os
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from core.screenshot_service import ScreenshotService as CoreScreenshotService
from services.database import DatabaseService
from services.activity import ActivityTrackingService
from utils.config import Config

# Setup logger
logger = logging.getLogger(__name__)

class ScreenshotManagementService:
    """
    Service for managing screenshots, including capture, storage, and retrieval.
    """
    
    def __init__(
        self,
        config: Optional[Config] = None,
        database: Optional[DatabaseService] = None,
        activity_tracking: Optional[ActivityTrackingService] = None,
        screenshot_service: Optional[CoreScreenshotService] = None
    ):
        """
        Initialize the screenshot management service.
        
        Args:
            config: Optional configuration object. If None, creates a new one.
            database: Optional database service. If None, creates a new one.
            activity_tracking: Optional activity tracking service. If used, 
                               screenshots will be linked to current activities.
            screenshot_service: Optional screenshot service. If None, creates a new one.
        """
        self.config = config or Config()
        self.database = database or DatabaseService()
        self.activity_tracking = activity_tracking
        
        # Get configuration values
        self.screenshot_interval = self.config.get("tracking.screenshot_interval", 300)
        self.screenshots_dir = self.config.get(
            "storage.screenshots_dir", 
            os.path.join(os.path.expanduser("~"), "TimeTracker", "screenshots")
        )
        
        # Ensure directory exists
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
        # Create or use provided screenshot service
        self.screenshot_service = screenshot_service or CoreScreenshotService(
            screenshot_interval=self.screenshot_interval
        )
        
        # Set up callbacks
        self.screenshot_service.set_screenshot_captured_callback(self._on_screenshot_captured)
        
        # State
        self.active = False
        self.screenshot_callbacks = []
        
    def start(self) -> bool:
        """
        Start automatic screenshot capturing.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.active:
            logger.warning("Screenshot service already running")
            return False
            
        # Start the screenshot service
        success = self.screenshot_service.start()
        if not success:
            logger.error("Failed to start screenshot service")
            return False
            
        self.active = True
        logger.info("Screenshot capturing started")
        
        return True
        
    def stop(self) -> bool:
        """
        Stop automatic screenshot capturing.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.active:
            logger.warning("Screenshot service not running")
            return False
            
        # Stop the screenshot service
        success = self.screenshot_service.stop()
        if not success:
            logger.error("Failed to stop screenshot service")
            return False
            
        self.active = False
        logger.info("Screenshot capturing stopped")
        
        return True
        
    async def capture_screenshot(self) -> Optional[Dict[str, Any]]:
        """
        Capture a screenshot immediately.
        
        Returns:
            dict: Screenshot metadata or None if failed
        """
        try:
            # Get current activity ID if available
            activity_log_id = None
            if self.activity_tracking:
                activity_status = self.activity_tracking.get_status()
                activity_log_id = activity_status.get("current_activity_id")
                
            # Capture screenshot
            screenshot = self.screenshot_service.capture_screenshot(activity_log_id)
            if not screenshot:
                logger.error("Failed to capture screenshot")
                return None
                
            # Store in database
            db_screenshot = self.database.create_screenshot(
                filepath=screenshot["filepath"],
                thumbnail_path=screenshot["thumbnail_path"],
                activity_log_id=activity_log_id
            )
            
            # Notify callbacks
            self._notify_screenshot_callbacks(db_screenshot)
            
            logger.info(f"Screenshot captured and stored with ID {db_screenshot['id']}")
            
            return db_screenshot
            
        except Exception as e:
            logger.error(f"Error capturing screenshot: {str(e)}")
            return None
            
    def get_recent_screenshots(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent screenshots.
        
        Args:
            limit: Maximum number of screenshots to return
            
        Returns:
            list: Recent screenshots
        """
        return self.database.get_screenshots(limit=limit)
        
    def get_activity_screenshots(self, activity_log_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get screenshots for a specific activity.
        
        Args:
            activity_log_id: Activity log ID
            limit: Maximum number of screenshots to return
            
        Returns:
            list: Screenshots for the activity
        """
        return self.database.get_screenshots(limit=limit, activity_log_id=activity_log_id)
        
    def set_screenshot_interval(self, interval: int) -> None:
        """
        Set the interval between automatic screenshots.
        
        Args:
            interval: Screenshot interval in seconds
        """
        self.screenshot_interval = interval
        self.screenshot_service.set_screenshot_interval(interval)
        self.config.set("tracking.screenshot_interval", interval)
        logger.info(f"Screenshot interval set to {interval} seconds")
        
    def add_screenshot_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Add a callback to be called when a screenshot is captured.
        
        Args:
            callback: Callback function that takes a screenshot dictionary
        """
        if callback not in self.screenshot_callbacks:
            self.screenshot_callbacks.append(callback)
            
    def remove_screenshot_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Remove a screenshot callback.
        
        Args:
            callback: Callback function to remove
        """
        if callback in self.screenshot_callbacks:
            self.screenshot_callbacks.remove(callback)
            
    def _notify_screenshot_callbacks(self, screenshot: Dict[str, Any]) -> None:
        """
        Notify all registered callbacks about a screenshot.
        
        Args:
            screenshot: Screenshot dictionary
        """
        for callback in self.screenshot_callbacks:
            try:
                callback(screenshot)
            except Exception as e:
                logger.error(f"Error in screenshot callback: {str(e)}")
                
    def _on_screenshot_captured(self, screenshot: Dict[str, Any]) -> None:
        """
        Callback for when a screenshot is captured by the core service.
        
        Args:
            screenshot: Screenshot metadata from the core service
        """
        try:
            # Get current activity ID if available
            activity_log_id = None
            if self.activity_tracking:
                activity_status = self.activity_tracking.get_status()
                activity_log_id = activity_status.get("current_activity_id")
                
            # Store in database
            db_screenshot = self.database.create_screenshot(
                filepath=screenshot["filepath"],
                thumbnail_path=screenshot["thumbnail_path"],
                activity_log_id=activity_log_id
            )
            
            # Notify callbacks
            self._notify_screenshot_callbacks(db_screenshot)
            
            logger.debug(f"Screenshot stored with ID {db_screenshot['id']}")
            
        except Exception as e:
            logger.error(f"Error processing captured screenshot: {str(e)}")
