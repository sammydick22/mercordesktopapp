"""
Script to patch the DatabaseService class with new methods.
"""
import os
import inspect
import importlib.util
from pathlib import Path

def patch_database_service():
    """
    Patches the DatabaseService class with methods from database_extensions.py
    """
    # Get directory of this script
    current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    
    # Import the extension module
    spec = importlib.util.spec_from_file_location(
        "database_extensions", 
        current_dir / "database_extensions.py"
    )
    extensions = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(extensions)
    
    # Import the database service
    from services.database import DatabaseService
    
    # Get all extension methods
    methods = inspect.getmembers(extensions, inspect.isfunction)
    
    # Add methods to DatabaseService class
    for name, method in methods:
        setattr(DatabaseService, name, method)
    
    print(f"Successfully added {len(methods)} methods to DatabaseService")

if __name__ == "__main__":
    patch_database_service()
