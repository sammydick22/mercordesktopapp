# Services package initialization

# Apply database extensions
try:
    from .database_extensions_patch import patch_database_service
    patch_database_service()
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Failed to apply database extensions: {str(e)}")

# Apply sync extensions
try:
    from .sync_extensions_patch import patch_sync_service
    patch_sync_service()
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"Failed to apply sync extensions: {str(e)}")
