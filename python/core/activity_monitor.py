"""
Activity monitoring module for tracking active windows and applications.
"""
import logging
import threading
import time
from datetime import datetime
import win32gui
import win32process
import psutil
import os

# Setup logger
logger = logging.getLogger(__name__)

class ActivityMonitor:
    """
    Monitors user activity by tracking active windows and applications.
    """
    
    def __init__(self, poll_interval=5, idle_threshold=300):
        """
        Initialize the activity monitor.
        
        Args:
            poll_interval: Seconds between activity checks
            idle_threshold: Seconds of inactivity before considered idle
        """
        self.poll_interval = poll_interval
        self.idle_threshold = idle_threshold
        self.active = False
        self.monitoring_thread = None
        self.last_activity = None
        self.idle_time = 0
        self.active_window_changed_callback = None
        self.idle_detected_callback = None
        self.activity_resumed_callback = None
        
    def start(self):
        """Start activity monitoring."""
        if self.active:
            logger.warning("Activity monitor already running")
            return False
            
        self.active = True
        self.monitoring_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitoring_thread.start()
        logger.info("Activity monitor started")
        return True
        
    def stop(self):
        """Stop activity monitoring."""
        if not self.active:
            logger.warning("Activity monitor not running")
            return False
            
        self.active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2.0)
            
        logger.info("Activity monitor stopped")
        return True
        
    def get_active_window_info(self):
        """
        Get information about the currently active window.
        
        Returns:
            dict: Active window information
        """
        try:
            # Get the foreground window
            hwnd = win32gui.GetForegroundWindow()
            
            # Get the process ID
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # Get window title
            window_title = win32gui.GetWindowText(hwnd)
            
            # Get process details
            try:
                process = psutil.Process(pid)
                process_name = process.name()
                executable_path = process.exe()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                process_name = "Unknown"
                executable_path = "Unknown"
                
            # Create window info dict
            window_info = {
                "window_title": window_title,
                "process_name": process_name,
                "executable_path": executable_path,
                "pid": pid,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return window_info
            
        except Exception as e:
            logger.error(f"Error getting active window info: {str(e)}")
            return {
                "window_title": "Error",
                "process_name": "Error",
                "executable_path": "Error",
                "pid": 0,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _monitor_loop(self):
        """Main monitoring loop that runs in a separate thread."""
        last_window_title = None
        last_process_name = None
        
        while self.active:
            try:
                # Get active window info
                window_info = self.get_active_window_info()
                current_window_title = window_info["window_title"]
                current_process_name = window_info["process_name"]
                
                # Check if window has changed or if we're resuming from idle
                window_changed = (current_window_title != last_window_title or 
                                 current_process_name != last_process_name)
                
                # Check for user activity
                if window_changed and current_window_title and current_process_name != "Error":
                    # Window changed, reset idle timer
                    self.idle_time = 0
                    
                    # If we were idle before, trigger activity resumed
                    if self.idle_time >= self.idle_threshold and self.activity_resumed_callback:
                        self.activity_resumed_callback()
                    
                    # Store new activity
                    self.last_activity = window_info
                    
                    # Call the callback if defined
                    if self.active_window_changed_callback:
                        self.active_window_changed_callback(window_info)
                    
                    logger.debug(f"Active window: {current_process_name} - {current_window_title}")
                    
                    # Update last known values
                    last_window_title = current_window_title
                    last_process_name = current_process_name
                else:
                    # Same window or error, increment idle time
                    self.idle_time += self.poll_interval
                    
                    # Check for idle state
                    if self.idle_time >= self.idle_threshold:
                        # Call the callback if defined
                        if self.idle_detected_callback:
                            self.idle_detected_callback(self.idle_time)
                            
                        logger.debug(f"User idle for {self.idle_time} seconds")
                
            except Exception as e:
                logger.error(f"Error in activity monitor loop: {str(e)}")
                
            # Sleep for the configured interval
            time.sleep(self.poll_interval)
    
    def set_active_window_changed_callback(self, callback):
        """Set callback for when active window changes."""
        self.active_window_changed_callback = callback
        
    def set_idle_detected_callback(self, callback):
        """Set callback for when user is detected as idle."""
        self.idle_detected_callback = callback
        
    def set_activity_resumed_callback(self, callback):
        """Set callback for when user activity resumes after idle."""
        self.activity_resumed_callback = callback
        
    def get_current_activity(self):
        """Get the current activity information."""
        return self.last_activity
        
    def get_idle_time(self):
        """Get the current idle time in seconds."""
        return self.idle_time
        
    def is_idle(self):
        """Check if the user is currently idle."""
        return self.idle_time >= self.idle_threshold
