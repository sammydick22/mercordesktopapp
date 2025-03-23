"""
Simple script to verify that extension methods are added to the classes.
"""
from services.database import DatabaseService
from services.sync import SyncService
from utils.config import Config

def print_methods(cls, prefix=""):
    """Print methods of a class with optional prefix filter."""
    methods = [m for m in dir(cls) if callable(getattr(cls, m)) and not m.startswith('__')]
    if prefix:
        methods = [m for m in methods if m.startswith(prefix)]
    methods.sort()
    return methods

# Initialize services
config = Config()
db = DatabaseService(config)
sync = SyncService(config, db)

# Check database extensions
db_methods = print_methods(db)
db_extension_methods = [
    "create_client",
    "get_client",
    "update_client",
    "delete_client",
    "get_clients",
    "create_project",
    "get_project",
    "update_project",
    "delete_project",
    "get_projects",
    "create_project_task",
    "get_project_task",
    "update_project_task",
    "delete_project_task",
    "get_project_tasks",
    "get_user_settings",
    "update_user_settings",
    "get_user_profile",
    "update_user_profile"
]

# Check if all extension methods exist in database service
print("\nChecking DatabaseService extensions:")
missing_db_methods = [m for m in db_extension_methods if m not in db_methods]
existing_db_methods = [m for m in db_extension_methods if m in db_methods]

print(f"Found {len(existing_db_methods)} out of {len(db_extension_methods)} expected methods:")
for method in existing_db_methods:
    print(f"✅ {method}")
    
if missing_db_methods:
    print("\nMissing methods:")
    for method in missing_db_methods:
        print(f"❌ {method}")

# Check sync extensions
sync_methods = print_methods(sync)
sync_extension_methods = [
    "_sync_clients",
    "_sync_projects",
    "_sync_project_tasks",
    "_sync_user_settings",
    "_sync_user_profile",
    "sync_all_extended",
    "get_sync_status_extended"
]

# Check if original methods are saved
print("\nChecking if original methods are saved:")
if hasattr(sync, "_original_sync_all"):
    print("✅ _original_sync_all exists")
else:
    print("❌ _original_sync_all missing")
    
if hasattr(sync, "_original_get_sync_status"):
    print("✅ _original_get_sync_status exists")
else:
    print("❌ _original_get_sync_status missing")

# Check if all extension methods exist in sync service
print("\nChecking SyncService extensions:")
missing_sync_methods = [m for m in sync_extension_methods if m not in sync_methods]
existing_sync_methods = [m for m in sync_extension_methods if m in sync_methods]

print(f"Found {len(existing_sync_methods)} out of {len(sync_extension_methods)} expected methods:")
for method in existing_sync_methods:
    print(f"✅ {method}")
    
if missing_sync_methods:
    print("\nMissing methods:")
    for method in missing_sync_methods:
        print(f"❌ {method}")

# Summary
total_expected = len(db_extension_methods) + len(sync_extension_methods)
total_found = len(existing_db_methods) + len(existing_sync_methods)

print(f"\nSummary: Found {total_found} out of {total_expected} expected extension methods")
if total_found == total_expected:
    print("✅ All extension methods were successfully added!")
else:
    print(f"❌ Missing {total_expected - total_found} extension methods")
