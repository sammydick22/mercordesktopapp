"""
Reset the sync state for activity logs to ensure all logs are synced.
"""
import os
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def reset_activity_logs_sync_state():
    """Reset the activity logs sync state to 0."""
    try:
        # Path to the sync state file
        config_dir = os.path.expanduser("~/TimeTracker/data")
        sync_file = os.path.join(config_dir, "sync_state.json")
        
        logger.info(f"Checking sync state file at: {sync_file}")
        
        if not os.path.exists(sync_file):
            logger.warning("Sync state file does not exist, nothing to reset")
            return False
        
        # Load the current sync state
        with open(sync_file, "r") as f:
            sync_state = json.load(f)
        
        # Log the current state
        logger.info(f"Current sync state: {sync_state}")
        
        # Check if activity_logs section exists
        if "activity_logs" not in sync_state:
            logger.warning("No activity_logs entry in sync state, nothing to reset")
            return False
        
        # Save the current last_id for reporting
        old_last_id = sync_state["activity_logs"].get("last_id", None)
        
        # Reset the activity_logs section
        sync_state["activity_logs"] = {
            "last_id": 0,
            "last_time": None
        }
        
        # Save the updated sync state
        with open(sync_file, "w") as f:
            json.dump(sync_state, f)
        
        logger.info(f"Reset activity logs sync state from {old_last_id} to 0")
        return True
    
    except Exception as e:
        logger.error(f"Error resetting sync state: {str(e)}")
        return False

if __name__ == "__main__":
    logger.info("=== RESETTING ACTIVITY LOGS SYNC STATE ===")
    success = reset_activity_logs_sync_state()
    logger.info(f"Reset {'successful' if success else 'failed'}")
