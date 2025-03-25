"""
Script to reset the sync state for specific data types in the TimeTracker application.
This will force a full resync of the specified data types.
"""
import os
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def reset_sync_state(data_types=None):
    """
    Reset the sync state for specific data types or all if not specified.
    
    Args:
        data_types: List of data types to reset ('screenshots', 'project_tasks', etc.)
                   If None, resets all data types.
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Path to the sync state file
    config_dir = os.path.expanduser("~/TimeTracker/data")
    sync_file = os.path.join(config_dir, "sync_state.json")
    
    try:
        # Check if sync state file exists
        if not os.path.exists(sync_file):
            logger.warning(f"Sync state file not found at: {sync_file}")
            print(f"⚠️ Sync state file not found at: {sync_file}")
            return False
            
        # Load current sync state
        with open(sync_file, "r") as f:
            sync_state = json.load(f)
            
        # Create backup of current sync state
        backup_file = sync_file + ".bak"
        with open(backup_file, "w") as f:
            json.dump(sync_state, f, indent=2)
            logger.info(f"Created sync state backup at: {backup_file}")
            print(f"✅ Created sync state backup at: {backup_file}")
            
        # Reset specified data types or all
        if data_types is None:
            # Reset all sync state
            sync_state = {}
            logger.info("Reset all sync state")
            print("✅ Reset all sync state")
        else:
            # Reset only specified data types
            for data_type in data_types:
                if data_type in sync_state:
                    del sync_state[data_type]
                    logger.info(f"Reset sync state for: {data_type}")
                    print(f"✅ Reset sync state for: {data_type}")
                else:
                    logger.info(f"No sync state found for: {data_type}")
                    print(f"ℹ️ No sync state found for: {data_type}")
                    
        # Save updated sync state
        with open(sync_file, "w") as f:
            json.dump(sync_state, f, indent=2)
            
        logger.info("Sync state reset complete")
        print("✅ Sync state reset complete")
        return True
        
    except Exception as e:
        logger.error(f"Error resetting sync state: {str(e)}")
        print(f"❌ Error resetting sync state: {str(e)}")
        return False

if __name__ == "__main__":
    print("Resetting TimeTracker sync state for screenshots and project_tasks...")
    reset_sync_state(['screenshots', 'project_tasks'])
    print("Done! Next sync operation will resync all screenshots and project tasks.")
