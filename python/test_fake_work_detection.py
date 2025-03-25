"""
Test script for fake work detection and dubious times recording.

This script tests the integration between FakeWorkDetector and the DatabaseService
to ensure that fake work detection timestamps are properly recorded and can be saved
to and synchronized with Supabase.
"""
import os
import sys
import json
import logging
import time
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.database import DatabaseService
from services.detect_fake_work import FakeWorkDetector

def test_fake_work_detection():
    """Test fake work detection and timestamp recording."""
    logger.info("Initializing database service...")
    db_service = DatabaseService()
    
    logger.info("Initializing fake work detector...")
    detector = FakeWorkDetector(
        # Use shorter thresholds for testing
        afk_threshold=5,
        mouse_variance_threshold=1,
        keystroke_variance_threshold=0.0001,
        # Disable actual monitoring for test
        log_active_window=False
    )
    
    # Simulate fake work being detected
    logger.info("Simulating fake work detection...")
    
    # Manually set fake_work_detected and add timestamps
    detector.fake_work_detected = True
    
    # Add test timestamps (2 minutes apart)
    now = datetime.now()
    timestamps = [
        now.replace(minute=now.minute - 2).isoformat(),
        now.isoformat()
    ]
    
    for ts in timestamps:
        detector.detection_timestamps.append(ts)
    
    logger.info(f"Added test timestamps: {timestamps}")
    
    # Create a test activity log
    logger.info("Creating test activity log...")
    activity_log = db_service.create_activity_log(
        window_title="Test Window",
        process_name="TestProcess.exe",
        executable_path="/path/to/test.exe"
    )
    
    if not activity_log:
        logger.error("Failed to create activity log")
        return False
    
    activity_id = activity_log["id"]
    logger.info(f"Created activity log with ID: {activity_id}")
    
    # Get the recorded timestamps from the detector
    detected_timestamps = detector.get_detection_timestamps()
    logger.info(f"Detector has recorded {len(detected_timestamps)} timestamps")
    
    # Update the activity log with the dubious times
    logger.info("Updating activity log with dubious times...")
    db_service.update_activity_log_dubious_times(activity_id, detected_timestamps[0])
    logger.info(f"Updated activity log with first timestamp: {detected_timestamps[0]}")
    
    # Add the second timestamp
    if len(detected_timestamps) > 1:
        db_service.update_activity_log_dubious_times(activity_id, detected_timestamps[1])
        logger.info(f"Updated activity log with second timestamp: {detected_timestamps[1]}")
    
    # Retrieve the activity log and verify the dubious times
    updated_log = db_service.get_activity_log(activity_id)
    
    if updated_log and updated_log.get("dubious_times"):
        logger.info("Retrieved activity log with dubious times")
        
        # Parse the JSON string to get the timestamps
        try:
            dubious_times = json.loads(updated_log["dubious_times"])
            
            logger.info(f"Found {len(dubious_times)} dubious times in the activity log")
            for i, ts in enumerate(dubious_times):
                logger.info(f"  Timestamp {i+1}: {ts}")
            
            # Check if all timestamps were saved
            if set(detected_timestamps) == set(dubious_times):
                logger.info("SUCCESS: All timestamps were correctly saved and retrieved")
                return True
            else:
                logger.error("FAILURE: Not all timestamps were correctly saved")
                logger.error(f"Expected: {detected_timestamps}")
                logger.error(f"Got: {dubious_times}")
                return False
        
        except json.JSONDecodeError:
            logger.error(f"Failed to parse dubious_times JSON: {updated_log['dubious_times']}")
            return False
    else:
        logger.error("FAILURE: No dubious times found in the activity log")
        logger.error(f"Updated log: {updated_log}")
        return False

if __name__ == "__main__":
    try:
        logger.info("Starting fake work detection test...")
        success = test_fake_work_detection()
        
        if success:
            logger.info("Test completed successfully!")
            sys.exit(0)
        else:
            logger.error("Test failed!")
            sys.exit(1)
    except Exception as e:
        logger.exception(f"Error during test: {str(e)}")
        sys.exit(1)
