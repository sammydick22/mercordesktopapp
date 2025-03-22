"""
Configuration management utility for the Time Tracker application.
"""
import os
import json
import logging
from typing import Any, Dict, Optional
import dotenv

# Setup logger
logger = logging.getLogger(__name__)

class Config:
    """
    Configuration manager for the Time Tracker application.
    
    Handles loading, saving, and accessing configuration settings.
    """
    
    # Class variable to implement the singleton pattern
    _instance = None
    
    def __new__(cls, config_path: Optional[str] = None):
        """
        Create a new Config instance or return the existing one.
        
        Args:
            config_path: Path to the configuration file.
                         If None, uses the default path.
        
        Returns:
            Config: The Config instance.
        """
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file.
                         If None, uses the default path.
        """
        # Skip initialization if already initialized
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        # Get the application data directory
        self.app_dir = self._get_app_data_dir()
        
        # Set config file path
        self.config_path = config_path or os.path.join(self.app_dir, 'config.json')
        
        # Load environment variables from .env file
        self._load_env_vars()
        
        # Load configuration
        self.config = self._load_config()
        
        # Set initialized flag
        self._initialized = True
        
    def _load_env_vars(self):
        """Load environment variables from .env file."""
        # Try to load from project directory
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
        if os.path.exists(env_path):
            dotenv.load_dotenv(env_path)
            logger.debug(f"Loaded environment variables from {env_path}")
        
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key: The configuration key. Can use dot notation for nested config.
            default: Default value if key doesn't exist.
            
        Returns:
            The configuration value, or the default if not found.
        """
        # Split key by dots for nested config
        parts = key.split('.')
        
        # Start with the full config
        current = self.config
        
        # Traverse the nested dictionaries
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
                
        return current
        
    def set(self, key: str, value: Any) -> None:
        """
        Set a configuration value.
        
        Args:
            key: The configuration key. Can use dot notation for nested config.
            value: The value to set.
        """
        # Split key by dots for nested config
        parts = key.split('.')
        
        # Start with the full config
        current = self.config
        
        # Traverse the nested dictionaries, creating them if needed
        for i, part in enumerate(parts[:-1]):
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
                
        # Set the value at the final level
        current[parts[-1]] = value
        
        # Save configuration to file
        self._save_config()
        
    def delete(self, key: str) -> bool:
        """
        Delete a configuration value.
        
        Args:
            key: The configuration key. Can use dot notation for nested config.
            
        Returns:
            bool: True if the key was deleted, False if it didn't exist.
        """
        # Split key by dots for nested config
        parts = key.split('.')
        
        # Start with the full config
        current = self.config
        
        # Traverse the nested dictionaries
        for i, part in enumerate(parts[:-1]):
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return False
                
        # Delete the key at the final level
        if parts[-1] in current:
            del current[parts[-1]]
            
            # Save configuration to file
            self._save_config()
            
            return True
        else:
            return False
            
    def _load_config(self) -> Dict[str, Any]:
        """
        Load configuration from file or create a default.
        
        Returns:
            dict: The loaded configuration.
        """
        try:
            # Check if config file exists
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    logger.debug(f"Configuration loaded from {self.config_path}")
                    return config
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            
        # Create default configuration
        return self._create_default_config()
        
    def _save_config(self) -> None:
        """Save configuration to file."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Write configuration to file
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
                
            logger.debug(f"Configuration saved to {self.config_path}")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            
    def _create_default_config(self) -> Dict[str, Any]:
        """
        Create default configuration.
        
        Returns:
            dict: The default configuration.
        """
        # Get Supabase URL and API key from environment variables
        supabase_url = os.environ.get('SUPABASE_URL', 'https://api.example.com')
        supabase_anon_key = os.environ.get('SUPABASE_ANON_KEY', '')
        
        default_config = {
            "api": {
                "url": supabase_url,
                "anon_key": supabase_anon_key
            },
            "auth": {
                "access_token": None,
                "refresh_token": None,
                "token_expiry": None
            },
            "tracking": {
                "auto_start": False,
                "capture_screenshots": True,
                "screenshot_interval": 300,  # 5 minutes
                "sync_interval": 600,  # 10 minutes
                "idle_threshold": 300,  # 5 minutes
                "poll_interval": 5  # 5 seconds
            },
            "ui": {
                "minimize_to_tray": True,
                "show_notifications": True
            },
            "storage": {
                "screenshots_dir": os.path.join(self.app_dir, "screenshots"),
                "database_dir": os.path.join(self.app_dir, "db"),
                "logs_dir": os.path.join(self.app_dir, "logs")
            },
            "debug": {
                "enabled": False,
                "log_level": "INFO"
            }
        }
        
        # Save default configuration
        self.config = default_config
        self._save_config()
        
        logger.info("Created default configuration")
        
        return default_config
        
    def _get_app_data_dir(self) -> str:
        """
        Get the application data directory based on the platform.
        
        Returns:
            str: The application data directory path.
        """
        system = os.name
        
        if system == 'nt':  # Windows
            app_data = os.environ.get('APPDATA')
            return os.path.join(app_data, 'TimeTracker')
        elif system == 'posix':  # macOS/Linux
            # macOS
            if os.path.exists('/Applications'):
                return os.path.expanduser('~/Library/Application Support/TimeTracker')
            # Linux
            else:
                return os.path.expanduser('~/.timetracker')
        else:
            # Fallback for other systems
            return os.path.expanduser('~/.timetracker')
            
    def ensure_dirs_exist(self) -> None:
        """Create required application directories if they don't exist."""
        dirs = [
            self.app_dir,
            self.get('storage.screenshots_dir'),
            self.get('storage.database_dir'),
            self.get('storage.logs_dir')
        ]
        
        for directory in dirs:
            try:
                if not os.path.exists(directory):
                    os.makedirs(directory)
                    logger.debug(f"Created directory: {directory}")
            except Exception as e:
                logger.error(f"Error creating directory {directory}: {e}")
                
    def get_app_dir(self) -> str:
        """
        Get the application data directory.
        
        Returns:
            str: The application data directory path.
        """
        return self.app_dir
        
    def get_all(self) -> Dict[str, Any]:
        """
        Get the entire configuration.
        
        Returns:
            dict: The complete configuration.
        """
        return self.config.copy()
