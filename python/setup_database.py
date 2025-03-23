import os
import logging
import asyncio
import sqlite3
from utils.config import Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def setup_database():
    """
    Set up the SQLite database with required tables based on schema from specifications.
    """
    try:
        # Initialize config
        config = Config()
        config.ensure_dirs_exist()
        
        # Get database directory and path
        db_dir = config.get('storage.database_dir')
        db_path = os.path.join(db_dir, 'timetracker.db')
        
        logger.info(f"Setting up database at {db_path}")
        
        # Connect to SQLite database (will create the file if it doesn't exist)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create activity_logs table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS activity_logs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          window_title TEXT NOT NULL,
          process_name TEXT NOT NULL,
          executable_path TEXT,
          start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          end_time TIMESTAMP,
          duration INTEGER,
          is_active BOOLEAN NOT NULL DEFAULT 1,
          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          synced BOOLEAN NOT NULL DEFAULT 0
        )
        ''')
        
        # Create index for faster queries on activity status
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_activity_logs_is_active 
        ON activity_logs(is_active)
        ''')
        
        # Create index for faster synchronization queries
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_activity_logs_synced 
        ON activity_logs(synced)
        ''')
        
        # Create screenshots table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS screenshots (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          filepath TEXT NOT NULL,
          thumbnail_path TEXT,
          timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          activity_log_id INTEGER,
          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          synced BOOLEAN NOT NULL DEFAULT 0,
          FOREIGN KEY (activity_log_id) REFERENCES activity_logs(id)
        )
        ''')
        
        # Create index for faster queries on activity association
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_screenshots_activity_log_id 
        ON screenshots(activity_log_id)
        ''')
        
        # Create index for faster synchronization queries
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_screenshots_synced 
        ON screenshots(synced)
        ''')
        
        # Create system_metrics table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_metrics (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          cpu_percent REAL,
          memory_percent REAL,
          battery_percent REAL,
          battery_charging BOOLEAN,
          timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          activity_log_id INTEGER,
          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          synced BOOLEAN NOT NULL DEFAULT 0,
          FOREIGN KEY (activity_log_id) REFERENCES activity_logs(id)
        )
        ''')
        
        # Create index for faster queries on activity association
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_system_metrics_activity_log_id 
        ON system_metrics(activity_log_id)
        ''')
        
        # Create index for faster synchronization queries
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_system_metrics_synced 
        ON system_metrics(synced)
        ''')
        
        # Create sync_status table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS sync_status (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          entity_type TEXT NOT NULL,
          last_sync_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          last_synced_id INTEGER NOT NULL DEFAULT 0,
          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create unique index on entity type
        cursor.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS idx_sync_status_entity_type 
        ON sync_status(entity_type)
        ''')
        
        # Create user_config table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_config (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          api_key TEXT,
          user_id TEXT,
          email TEXT,
          poll_interval INTEGER NOT NULL DEFAULT 5,
          idle_threshold INTEGER NOT NULL DEFAULT 300,
          screenshot_interval INTEGER NOT NULL DEFAULT 300,
          sync_interval INTEGER NOT NULL DEFAULT 600,
          collect_metrics BOOLEAN NOT NULL DEFAULT 1,
          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create clients table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          contact_name TEXT,
          email TEXT,
          phone TEXT,
          address TEXT,
          notes TEXT,
          is_active INTEGER NOT NULL DEFAULT 1,
          user_id TEXT,
          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          synced INTEGER NOT NULL DEFAULT 0
        )
        ''')
        
        # Create index for faster synchronization queries on clients
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_clients_synced 
        ON clients(synced)
        ''')
        
        # Create projects table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          description TEXT,
          client_id TEXT,
          color TEXT,
          hourly_rate REAL,
          is_billable INTEGER NOT NULL DEFAULT 1,
          is_active INTEGER NOT NULL DEFAULT 1,
          user_id TEXT,
          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          synced INTEGER NOT NULL DEFAULT 0,
          FOREIGN KEY (client_id) REFERENCES clients(id)
        )
        ''')
        
        # Create index for faster synchronization queries on projects
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_projects_synced 
        ON projects(synced)
        ''')
        
        # Create project tasks table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_tasks (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          description TEXT,
          project_id TEXT NOT NULL,
          estimated_hours REAL,
          is_active INTEGER NOT NULL DEFAULT 1,
          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          synced INTEGER NOT NULL DEFAULT 0,
          FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        ''')
        
        # Create index for faster synchronization queries on tasks
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_project_tasks_synced 
        ON project_tasks(synced)
        ''')
        
        # Create user settings table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
          user_id TEXT PRIMARY KEY,
          screenshot_interval INTEGER DEFAULT 600,
          screenshot_quality TEXT DEFAULT 'medium',
          auto_sync_interval INTEGER DEFAULT 300,
          idle_detection_timeout INTEGER DEFAULT 300,
          theme TEXT DEFAULT 'system',
          notifications_enabled INTEGER DEFAULT 1,
          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          synced INTEGER NOT NULL DEFAULT 0
        )
        ''')
        
        # Create index for faster synchronization queries on settings
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_user_settings_synced 
        ON user_settings(synced)
        ''')
        
        # Create user profiles table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
          user_id TEXT PRIMARY KEY,
          name TEXT,
          email TEXT,
          timezone TEXT DEFAULT 'UTC',
          hourly_rate REAL DEFAULT 0,
          avatar_url TEXT,
          created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
          synced INTEGER NOT NULL DEFAULT 0
        )
        ''')
        
        # Create index for faster synchronization queries on profiles
        cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_user_profiles_synced 
        ON user_profiles(synced)
        ''')
        
        # Initialize sync_status for each entity type if not already present
        for entity_type in ['activity_logs', 'screenshots', 'system_metrics']:
            cursor.execute('''
            INSERT OR IGNORE INTO sync_status (entity_type, last_sync_time, last_synced_id) 
            VALUES (?, CURRENT_TIMESTAMP, 0)
            ''', (entity_type,))
        
        # Commit the changes
        conn.commit()
        logger.info("Database schema created successfully")
        
        # Close the connection
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error setting up database: {str(e)}")
        return False

async def main():
    success = await setup_database()
    if success:
        logger.info("✅ Database setup completed successfully!")
    else:
        logger.error("❌ Database setup failed!")

if __name__ == "__main__":
    asyncio.run(main())
