"""
Script to patch the SyncService class with new methods.
"""
import os
import inspect
import importlib.util
from pathlib import Path
from datetime import datetime

def patch_sync_service():
    """
    Patches the SyncService class with methods from sync_extensions.py
    """
    # Get directory of this script
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    
    # Import the extension module
    spec = importlib.util.spec_from_file_location(
        "sync_extensions", 
        current_dir / "sync_extensions.py"
    )
    extensions = importlib.util.module_from_spec(spec)
    # Add missing datetime import
    extensions.datetime = datetime
    spec.loader.exec_module(extensions)
    
    # Import the sync service
    from services.sync import SyncService
    
    # Save original methods
    SyncService._original_sync_all = SyncService.sync_all
    SyncService._original_get_sync_status = SyncService.get_sync_status
    
    # Get all extension methods
    methods = inspect.getmembers(extensions, inspect.isfunction)
    
    # Add methods to SyncService class
    for name, method in methods:
        setattr(SyncService, name, method)
    
    # Replace sync_all with the extended version
    SyncService.sync_all = SyncService.sync_all_extended
    
    # Replace get_sync_status with the extended version
    SyncService.get_sync_status = SyncService.get_sync_status_extended
    
    print(f"Successfully patched SyncService with {len(methods)} methods")

if __name__ == "__main__":
    patch_sync_service()
