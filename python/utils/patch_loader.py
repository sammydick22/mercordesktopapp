"""
Utility to load database service extensions and patches.
"""
import logging
import importlib
import inspect

logger = logging.getLogger(__name__)

def apply_patches_to_class(target_class, patch_module_name):
    """
    Apply methods from a patch module to a target class.
    
    Args:
        target_class: The class to patch
        patch_module_name: The name of the module with patch methods
    
    Returns:
        int: Number of methods successfully patched
    """
    try:
        # Import the patch module
        patch_module = importlib.import_module(patch_module_name)
        
        # Get all functions from the module
        functions = inspect.getmembers(patch_module, inspect.isfunction)
        
        patched_count = 0
        
        # Apply each function to the target class
        for name, func in functions:
            if name.startswith('_'):
                continue  # Skip private/internal functions
                
            # Add the function as a method to the target class
            setattr(target_class, name, func)
            patched_count += 1
            
        logger.info(f"Successfully added {patched_count} methods to {target_class.__name__}")
        return patched_count
        
    except ImportError:
        logger.warning(f"Patch module {patch_module_name} not found")
        return 0
    except Exception as e:
        logger.error(f"Error applying patches from {patch_module_name}: {str(e)}")
        return 0
