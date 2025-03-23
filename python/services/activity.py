"""
Activity tracking service for monitoring and recording user activity.
"""
import logging
import os
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime

from core.activity_monitor import ActivityMonitor
from services.database import DatabaseService
from utils.config import Config

# Setup logger
logger = logging.getLogger(__name__)

class ActivityTrackingService:
    """
    Service for tracking and recording user activity.
    """
    
    def __init__(
        self,
        config: Optional[Config] = None,
        database: Optional[DatabaseService] = None,
        activity_monitor: Optional[ActivityMonitor] = None
    ):
        """
        Initialize the activity tracking service.
        
        Args:
            config: Optional configuration object. If None, creates a new one.
            database: Optional database service. If None, creates a new one.
            activity_monitor: Optional activity monitor. If None, creates a new one.
        """
        self.config = config or Config()
        self.database = database or DatabaseService()
        
        # Get configuration values
        self.poll_interval = self.config.get("tracking.poll_interval", 5)
        self.idle_threshold = self.config.get("tracking.idle_threshold", 300)
        
        # Create or use provided activity monitor
        self.activity_monitor = activity_monitor or ActivityMonitor(
            poll_interval=self.poll_interval,
            idle_threshold=self.idle_threshold
        )
        
        # Set up callbacks
        self.activity_monitor.set_active_window_changed_callback(self._on_active_window_changed)
        self.activity_monitor.set_idle_detected_callback(self._on_idle_detected)
        self.activity_monitor.set_activity_resumed_callback(self._on_activity_resumed)
        
        # Current activity state
        self.current_activity_id = None
        self.tracking_enabled = False
        self.activity_callbacks = []
        
    def start(self) -> bool:
        """
        Start activity tracking.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.tracking_enabled:
            logger.warning("Activity tracking already enabled")
            return False
            
        # Start the activity monitor
        success = self.activity_monitor.start()
        if not success:
            logger.error("Failed to start activity monitor")
            return False
            
        self.tracking_enabled = True
        logger.info("Activity tracking started")
        
        return True
        
    def stop(self) -> bool:
        """
        Stop activity tracking.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if not self.tracking_enabled:
            logger.warning("Activity tracking not enabled")
            return False
            
        # Stop the activity monitor
        success = self.activity_monitor.stop()
        if not success:
            logger.error("Failed to stop activity monitor")
            return False
            
        # Close any active activity
        if self.current_activity_id:
            self._stop_current_activity()
            
        self.tracking_enabled = False
        logger.info("Activity tracking stopped")
        
        return True
        
    def pause(self) -> bool:
        """
        Pause activity tracking without stopping the monitor.
        
        Returns:
            bool: True if paused successfully, False otherwise
        """
        if not self.tracking_enabled:
            logger.warning("Activity tracking not enabled")
            return False
            
        # Just close the current activity
        if self.current_activity_id:
            self._stop_current_activity()
            
        logger.info("Activity tracking paused")
        
        return True
        
    def resume(self) -> bool:
        """
        Resume activity tracking after being paused.
        
        Returns:
            bool: True if resumed successfully, False otherwise
        """
        if not self.tracking_enabled:
            logger.warning("Activity tracking not enabled, start it first")
            return False
            
        # Get current window info and start tracking it
        window_info = self.activity_monitor.get_current_activity()
        if window_info:
            self._start_new_activity(window_info)
            logger.info("Activity tracking resumed")
            return True
        else:
            logger.warning("No active window detected")
            return False
            
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current activity tracking status.
        
        Returns:
            dict: Activity tracking status
        """
        return {
            "enabled": self.tracking_enabled,
            "current_activity_id": self.current_activity_id,
            "idle": self.activity_monitor.is_idle(),
            "idle_time": self.activity_monitor.get_idle_time(),
            "idle_threshold": self.idle_threshold
        }
        
    def get_recent_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent activity logs.
        
        Args:
            limit: Maximum number of activities to return
            
        Returns:
            list: Recent activity logs
        """
        return self.database.get_activity_logs(limit=limit)
        
    def add_activity_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Add a callback to be called when activity changes.
        
        Args:
            callback: Callback function that takes an activity dictionary
        """
        if callback not in self.activity_callbacks:
            self.activity_callbacks.append(callback)
            
    def remove_activity_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """
        Remove an activity callback.
        
        Args:
            callback: Callback function to remove
        """
        if callback in self.activity_callbacks:
            self.activity_callbacks.remove(callback)
            
    def _notify_activity_callbacks(self, activity: Dict[str, Any]) -> None:
        """
        Notify all registered callbacks about an activity update.
        
        Args:
            activity: Activity dictionary
        """
        for callback in self.activity_callbacks:
            try:
                callback(activity)
            except Exception as e:
                logger.error(f"Error in activity callback: {str(e)}")
                
    def _on_active_window_changed(self, window_info: Dict[str, Any]) -> None:
        """
        Callback for when the active window changes.
        
        Args:
            window_info: Information about the new active window
        """
        if not self.tracking_enabled:
            return
            
        # Stop current activity if there is one
        if self.current_activity_id:
            self._stop_current_activity()
            
        # Start new activity
        self._start_new_activity(window_info)
        
    def _on_idle_detected(self, idle_time: int) -> None:
        """
        Callback for when idle state is detected.
        
        Args:
            idle_time: Time in seconds the user has been idle
        """
        if not self.tracking_enabled or not self.current_activity_id:
            return
            
        # Stop current activity when idle detected
        self._stop_current_activity()
        logger.debug(f"User idle for {idle_time} seconds, stopped activity tracking")
        
    def _on_activity_resumed(self) -> None:
        """Callback for when activity resumes after idle."""
        if not self.tracking_enabled:
            return
            
        # Get current window info and start tracking it
        window_info = self.activity_monitor.get_current_activity()
        if window_info:
            self._start_new_activity(window_info)
            logger.debug("Activity resumed after idle period")
            
    def _start_new_activity(self, window_info: Dict[str, Any]) -> None:
        """
        Start tracking a new activity.
        
        Args:
            window_info: Information about the window to track
        """
        try:
            # Create activity log in database
            activity = self.database.create_activity_log(
                window_title=window_info.get("window_title", "Unknown"),
                process_name=window_info.get("process_name", "Unknown"),
                executable_path=window_info.get("executable_path", "Unknown")
            )
            
            # Store the activity ID
            self.current_activity_id = activity["id"]
            
            # Notify callbacks
            self._notify_activity_callbacks(activity)
            
            logger.debug(f"Started new activity: {activity['process_name']} - {activity['window_title']}")
            
        except Exception as e:
            logger.error(f"Error starting new activity: {str(e)}")
            
    def _stop_current_activity(self) -> None:
        """Stop the current activity."""
        try:
            if not self.current_activity_id:
                return
                
            # Update activity log in database
            activity = self.database.end_activity_log(self.current_activity_id)
            
            # Clear the activity ID
            self.current_activity_id = None
            
            # Notify callbacks
            if activity:
                self._notify_activity_callbacks(activity)
                
            logger.debug("Stopped current activity")
            
        except Exception as e:
            logger.error(f"Error stopping current activity: {str(e)}")
