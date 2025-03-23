"""
Screenshot service for capturing and managing screenshots.
"""
import logging
import threading
import time
import os
from datetime import datetime
import mss
from PIL import Image
import io

# Setup logger
logger = logging.getLogger(__name__)

class ScreenshotService:
    """
    Service for capturing and managing screenshots.
    """
    
    def __init__(self, screenshot_interval=300):
        """
        Initialize the screenshot service.
        
        Args:
            screenshot_interval: Seconds between automatic screenshots
        """
        self.screenshot_interval = screenshot_interval
        self.active = False
        self.screenshot_thread = None
        self.screenshot_captured_callback = None
        self.screenshots_dir = self._get_screenshots_dir()
        
    def start(self):
        """Start automatic screenshot capturing."""
        if self.active:
            logger.warning("Screenshot service already running")
            return False
            
        self.active = True
        self.screenshot_thread = threading.Thread(target=self._screenshot_loop, daemon=True)
        self.screenshot_thread.start()
        logger.info("Screenshot service started")
        return True
        
    def stop(self):
        """Stop automatic screenshot capturing."""
        if not self.active:
            logger.warning("Screenshot service not running")
            return False
            
        self.active = False
        if self.screenshot_thread:
            self.screenshot_thread.join(timeout=2.0)
            
        logger.info("Screenshot service stopped")
        return True
        
    def capture_screenshot(self, time_entry_id=None):
        """
        Capture a screenshot immediately.
        
        Args:
            time_entry_id: Optional time entry ID to associate with the screenshot
            
        Returns:
            dict: Screenshot metadata
        """
        try:
            timestamp = datetime.utcnow()
            filename = f"screenshot_{timestamp.strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Capture the screenshot
            with mss.mss() as sct:
                monitor = sct.monitors[1]  # Primary monitor
                sct_img = sct.grab(monitor)
                
                # Save the image
                img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")
                img.save(filepath)
                logger.debug(f"Screenshot saved to {filepath}")
                
                # Create thumbnail
                thumbnail_path = self._create_thumbnail(img, filepath)
                
                # Create screenshot metadata
                screenshot = {
                    "timestamp": timestamp.isoformat(),
                    "filepath": filepath,
                    "thumbnail_path": thumbnail_path,
                    "time_entry_id": time_entry_id
                }
                
                # Call the callback if defined
                if self.screenshot_captured_callback:
                    self.screenshot_captured_callback(screenshot)
                
                return screenshot
        
        except Exception as e:
            logger.error(f"Error capturing screenshot: {str(e)}")
            return None
    
    def _screenshot_loop(self):
        """Main screenshot loop that runs in a separate thread."""
        while self.active:
            try:
                # Capture a screenshot
                self.capture_screenshot()
                
            except Exception as e:
                logger.error(f"Error in screenshot loop: {str(e)}")
                
            # Sleep for the configured interval
            time.sleep(self.screenshot_interval)
    
    def _create_thumbnail(self, img, filepath, size=(200, 200)):
        """
        Create a thumbnail of the given screenshot.
        
        Args:
            img: PIL Image object
            filepath: Path to the original screenshot
            size: Thumbnail dimensions
            
        Returns:
            str: Path to the created thumbnail
        """
        try:
            # Generate thumbnail filename
            thumbnail_path = filepath.replace('.png', '_thumb.png')
            
            # Create thumbnail
            thumb = img.copy()
            thumb.thumbnail(size)
            thumb.save(thumbnail_path)
            
            logger.debug(f"Thumbnail saved to {thumbnail_path}")
            return thumbnail_path
            
        except Exception as e:
            logger.error(f"Error creating thumbnail: {str(e)}")
            return None
    
    def _get_screenshots_dir(self):
        """
        Get or create the screenshots directory.
        
        Returns:
            str: Path to the screenshots directory
        """
        screenshots_dir = os.path.join(os.path.expanduser("~"), "TimeTracker", "screenshots")
        os.makedirs(screenshots_dir, exist_ok=True)
        return screenshots_dir
        
    def set_screenshot_captured_callback(self, callback):
        """Set callback for when a screenshot is captured."""
        self.screenshot_captured_callback = callback
        
    def set_screenshot_interval(self, interval):
        """Set the interval between automatic screenshots."""
        self.screenshot_interval = interval
