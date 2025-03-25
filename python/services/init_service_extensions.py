"""
Initializer script to add extensions to database and sync services.
"""
import logging
import functools
from typing import Optional

from .database import DatabaseService
from .supabase_sync import SupabaseSyncService

# Import extension methods
from .database_extensions import (
    get_unsynchronized_projects,
    get_unsynchronized_clients,
    get_project_tasks,
    update_project_sync_status,
    update_client_sync_status,
    get_unsynchronized_user_profiles,
    get_unsynchronized_user_settings,
    get_unsynchronized_project_tasks,
    update_user_profile_sync_status,
    update_user_setting_sync_status,
    update_project_task_sync_status
)
from .supabase_sync_extensions import (
    sync_clients,
    sync_projects,
    sync_project_tasks,
    sync_all_project_tasks,
    sync_user_profiles,
    sync_user_settings,
    sync_time_entries,
    extended_sync_all
)

# Setup logger
logger = logging.getLogger(__name__)

def init_service_extensions():
    """Initialize service extensions by patching the classes with new methods."""
    logger.info("Initializing service extensions")
    
    # Add methods to DatabaseService
    setattr(DatabaseService, "get_unsynchronized_projects", get_unsynchronized_projects)
    setattr(DatabaseService, "get_unsynchronized_clients", get_unsynchronized_clients)
    setattr(DatabaseService, "get_project_tasks", get_project_tasks)
    setattr(DatabaseService, "update_project_sync_status", update_project_sync_status)
    setattr(DatabaseService, "update_client_sync_status", update_client_sync_status)
    # Add new methods for user profiles, settings, and tasks
    setattr(DatabaseService, "get_unsynchronized_user_profiles", get_unsynchronized_user_profiles)
    setattr(DatabaseService, "get_unsynchronized_user_settings", get_unsynchronized_user_settings)
    setattr(DatabaseService, "get_unsynchronized_project_tasks", get_unsynchronized_project_tasks)
    setattr(DatabaseService, "update_user_profile_sync_status", update_user_profile_sync_status)
    setattr(DatabaseService, "update_user_setting_sync_status", update_user_setting_sync_status)
    setattr(DatabaseService, "update_project_task_sync_status", update_project_task_sync_status)
    
    # Add methods to SupabaseSyncService
    setattr(SupabaseSyncService, "sync_clients", sync_clients)
    setattr(SupabaseSyncService, "sync_projects", sync_projects)
    setattr(SupabaseSyncService, "sync_project_tasks", sync_project_tasks)
    # Add new sync methods
    setattr(SupabaseSyncService, "sync_all_project_tasks", sync_all_project_tasks)
    setattr(SupabaseSyncService, "sync_user_profiles", sync_user_profiles)
    setattr(SupabaseSyncService, "sync_user_settings", sync_user_settings)
    setattr(SupabaseSyncService, "sync_time_entries", sync_time_entries)
    
    # Patch the sync_all method with our extended version
    # This correctly applies the decorator to the original method 
    # and assigns the result back to the class
    SupabaseSyncService.sync_all = extended_sync_all(SupabaseSyncService.sync_all)
    
    # Log success
    db_method_count = 11  # 5 original + 6 new methods
    sync_method_count = 7  # 3 original + 4 new methods
    logger.info(f"Successfully added {db_method_count} methods to DatabaseService")
    logger.info(f"Successfully patched SyncService with {sync_method_count} methods")

# Initialize extensions when this module is imported
init_service_extensions()
