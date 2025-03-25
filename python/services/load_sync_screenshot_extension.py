"""
Utility to load the screenshot sync extension into the SupabaseSyncService.
"""
import logging
import os
from pathlib import Path
import importlib.util
from typing import Any

logger = logging.getLogger(__name__)

def load_screenshot_extension(cls: Any) -> bool:
    """
    Explicitly loads the screenshot sync extension into the provided class.
    
    Args:
        cls: The class to extend (SupabaseSyncService)
        
    Returns:
        bool: True if successful
    """
    try:
        # Get the path to the extension file
        current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        extension_path = current_dir / "sync_screenshots_extension.py"
        
        if not extension_path.exists():
            logger.error(f"Screenshot extension not found at: {extension_path}")
            return False
            
        # Import the extension module
        spec = importlib.util.spec_from_file_location(
            "sync_screenshots_extension", 
            extension_path
        )
        if not spec or not spec.loader:
            logger.error("Failed to create module spec for screenshot extension")
            return False
            
        extension = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(extension)
        
        # Get the functions from the extension
        if not hasattr(extension, "sync_screenshots"):
            logger.error("sync_screenshots function not found in extension")
            return False
            
        # Also check for get_current_org_id method
        if hasattr(extension, "get_current_org_id"):
            # Add the get_current_org_id method to the class
            setattr(cls, "get_current_org_id", extension.get_current_org_id)
            logger.info("Successfully loaded get_current_org_id method")
            
        # Replace the sync_screenshots method in the class
        setattr(cls, "sync_screenshots", extension.sync_screenshots)
        logger.info("Successfully loaded screenshot sync extension")
        
        return True
    except Exception as e:
        logger.error(f"Error loading screenshot extension: {str(e)}")
        return False
