"""
Super simple check for extension methods.
"""
import logging
import sys

# Configure logging to output to stdout
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                   stream=sys.stdout)

print("Starting simple check...")
print("Python version:", sys.version)

print("\nImporting services:")
try:
    from services.database import DatabaseService
    print("✓ Imported DatabaseService")
except Exception as e:
    print(f"✗ Failed to import DatabaseService: {e}")

try:
    from services.sync import SyncService
    print("✓ Imported SyncService")
except Exception as e:
    print(f"✗ Failed to import SyncService: {e}")

try:
    from utils.config import Config
    print("✓ Imported Config")
except Exception as e:
    print(f"✗ Failed to import Config: {e}")

print("\nInitializing services:")
try:
    config = Config()
    print("✓ Initialized Config")
except Exception as e:
    print(f"✗ Failed to initialize Config: {e}")

try:
    db = DatabaseService(config)
    print("✓ Initialized DatabaseService")
except Exception as e:
    print(f"✗ Failed to initialize DatabaseService: {e}")

print("\nChecking client-related methods:")
try:
    client_method = getattr(db, "create_client", None)
    if client_method is not None and callable(client_method):
        print("✓ create_client method exists")
    else:
        print("✗ create_client method does not exist")
except Exception as e:
    print(f"✗ Error checking create_client: {e}")

print("\nChecking sync-related methods:")
try:
    sync = SyncService(config, db)
    print("✓ Initialized SyncService")
    
    if hasattr(sync, "_sync_clients"):
        print("✓ _sync_clients method exists")
    else:
        print("✗ _sync_clients method does not exist")
        
    if hasattr(sync, "_original_sync_all"):
        print("✓ _original_sync_all attribute exists")
    else:
        print("✗ _original_sync_all attribute does not exist")
except Exception as e:
    print(f"✗ Error initializing SyncService: {e}")

print("\nSimple check completed.")
