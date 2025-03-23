import asyncio
import logging
import time
import random
from datetime import datetime
from services.database import DatabaseService
from services.activity import ActivityTrackingService
from services.screenshots import ScreenshotManagementService
from utils.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_activity_tracking():
    """Test the activity tracking and screenshot functionality."""
    print("\n==== Testing Activity Tracking and Screenshots ====\n")
    
    try:
        # Initialize services
        config = Config()
        db_service = DatabaseService(config)
        activity_service = ActivityTrackingService(config, db_service)
        screenshot_service = ScreenshotManagementService(config, db_service, activity_service)
        
        print("Services initialized")
        
        # Start tracking
        print("Starting activity tracking...")
        if activity_service.start():
            print("✅ Activity tracking started")
        else:
            print("❌ Failed to start activity tracking")
            return False
            
        # Test creating an activity
        window_title = f"Test Window - {datetime.now().strftime('%H:%M:%S')}"
        process_name = "python.exe"
        
        print(f"Creating test activity manually: {window_title}")
        window_info = {
            "window_title": window_title,
            "process_name": process_name,
            "executable_path": "C:/python.exe"
        }
        
        # Manually trigger window change
        activity_service._on_active_window_changed(window_info)
        
        # Wait a bit
        print("Activity tracking for 5 seconds...")
        for i in range(5):
            await asyncio.sleep(1)
            print(".", end="", flush=True)
        print("\n")
            
        # Take a screenshot
        print("Taking a screenshot...")
        screenshot = await screenshot_service.capture_screenshot()
        
        if screenshot:
            print(f"✅ Screenshot captured: {screenshot.get('filepath')}")
            print(f"   Thumbnail: {screenshot.get('thumbnail_path')}")
        else:
            print("❌ Failed to capture screenshot")
            
        # Pause tracking
        print("Pausing activity tracking...")
        if activity_service.pause():
            print("✅ Activity tracking paused")
        else:
            print("❌ Failed to pause activity tracking")
        
        await asyncio.sleep(1)
            
        # Get activity status
        status = activity_service.get_status()
        print(f"Activity status: {status}")
            
        # Test getting activity logs
        print("\nRetrieving recent activity logs...")
        logs = activity_service.get_recent_activities(limit=5)
        
        if logs:
            print(f"✅ Retrieved {len(logs)} activity logs")
            for log in logs:
                start_time = log.get('start_time', '')
                title = log.get('window_title', '')
                duration = log.get('duration', 0)
                print(f"  - [{start_time}] {title} ({duration} seconds)")
        else:
            print("❌ Failed to retrieve activity logs or no logs found")
        
        # Test getting screenshots
        print("\nRetrieving recent screenshots...")
        screenshots = screenshot_service.get_recent_screenshots(limit=5)
        
        if screenshots:
            print(f"✅ Retrieved {len(screenshots)} screenshots")
            for ss in screenshots:
                timestamp = ss.get('timestamp', '')
                path = ss.get('filepath', '')
                print(f"  - [{timestamp}] {path}")
        else:
            print("❌ Failed to retrieve screenshots or no screenshots found")
            
        # Stop tracking
        print("\nStopping activity tracking...")
        if activity_service.stop():
            print("✅ Activity tracking stopped")
        else:
            print("❌ Failed to stop activity tracking")
            
        print("\nActivity tracking test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error in activity tracking test: {str(e)}")
        logger.error(f"Error in activity tracking test: {str(e)}")
        raise
    finally:
        # Clean up
        if 'db_service' in locals():
            db_service.close()

async def main():
    try:
        await test_activity_tracking()
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        print(f"\nTest failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
