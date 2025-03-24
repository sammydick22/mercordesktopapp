"""
Database service for managing the local SQLite database.
"""
import os
import sqlite3
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from utils.config import Config

# Setup logger
logger = logging.getLogger(__name__)

class DatabaseService:
    """
    Service for managing the local SQLite database.
    
    Handles database initialization, migrations, and CRUD operations.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the database service.
        
        Args:
            config: Optional configuration object. If None, creates a new one.
        """
        self.config = config or Config()
        
        # Get database directory from config
        self.db_dir = self.config.get("storage.database_dir")
        if not self.db_dir:
            self.db_dir = os.path.join(self.config.get_app_dir(), "db")
            
        # Set database file path
        self.db_path = os.path.join(self.db_dir, "timetracker.db")
        
        # Create database directory if it doesn't exist
        os.makedirs(self.db_dir, exist_ok=True)
        
        # Store thread ID for safety checks
        import threading
        self._init_thread_id = threading.get_ident()
        self._thread_local = threading.local()
        
        # Initialize database
        self.conn = None
        self._initialize_db()
        
    def _get_connection(self):
        """
        Get a SQLite connection for the current thread.
        
        Returns:
            sqlite3.Connection: A connection object for the current thread
        """
        import threading
        current_thread_id = threading.get_ident()
        
        # Check if we're in the init thread
        if current_thread_id == self._init_thread_id:
            if self.conn is None:
                self.conn = sqlite3.connect(self.db_path)
                self.conn.execute("PRAGMA foreign_keys = ON")
            return self.conn
        
        # For other threads, store connection in thread_local
        if not hasattr(self._thread_local, 'conn'):
            # Create a new connection for this thread
            self._thread_local.conn = sqlite3.connect(self.db_path)
            # Enable foreign keys
            self._thread_local.conn.execute("PRAGMA foreign_keys = ON")
            
        return self._thread_local.conn
    
    def _initialize_db(self) -> None:
        """Initialize the database by creating the connection and tables."""
        try:
            # Connect to database using thread-safe method
            conn = self._get_connection()
            
            # Create tables if they don't exist
            self._create_tables()
            
            logger.info(f"Database initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
            
    def _create_tables(self) -> None:
        """Create database tables if they don't exist."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Organizations table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS organizations (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                settings TEXT,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
            ''')
            
            # Organization members table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS org_members (
                id TEXT PRIMARY KEY,
                org_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (org_id) REFERENCES organizations(id),
                UNIQUE(org_id, user_id)
            )
            ''')
            
            # Activity logs table
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
                synced BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Screenshots table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS screenshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filepath TEXT NOT NULL,
                thumbnail_path TEXT,
                activity_log_id INTEGER,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                synced BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (activity_log_id) REFERENCES activity_logs(id)
            )
            ''')
            
            # System metrics table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cpu_percent REAL,
                memory_percent REAL,
                battery_percent REAL,
                battery_charging BOOLEAN,
                activity_log_id INTEGER,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                synced BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (activity_log_id) REFERENCES activity_logs(id)
            )
            ''')
            
            # Sync status table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sync_status (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type TEXT NOT NULL UNIQUE,
                last_synced_id INTEGER NOT NULL DEFAULT 0,
                last_sync_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Clients table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                contact_name TEXT,
                email TEXT,
                phone TEXT,
                address TEXT,
                notes TEXT,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                synced BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                user_id TEXT NOT NULL
            )
            ''')
            
            # Projects table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                client_id TEXT,
                description TEXT,
                color TEXT,
                hourly_rate REAL DEFAULT 0,
                is_billable BOOLEAN NOT NULL DEFAULT 1,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                synced BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
            ''')
            
            # Create indices
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_logs_is_active ON activity_logs(is_active)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_activity_logs_synced ON activity_logs(synced)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_screenshots_activity_log_id ON screenshots(activity_log_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_screenshots_synced ON screenshots(synced)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_metrics_activity_log_id ON system_metrics(activity_log_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_system_metrics_synced ON system_metrics(synced)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_org_members_user_id ON org_members(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(name)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_client_id ON projects(client_id)')
            
            # Initialize sync status for each entity type if not exists
            self._ensure_sync_status("activity_logs")
            self._ensure_sync_status("screenshots")
            self._ensure_sync_status("system_metrics")
            
            # Commit changes
            self.conn.commit()
            
            logger.debug("Database tables created")
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            self.conn.rollback()
            raise
            
    def _ensure_sync_status(self, entity_type: str) -> None:
        """
        Ensure sync status exists for the given entity type.
        
        Args:
            entity_type: The entity type to check
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT COUNT(*) FROM sync_status WHERE entity_type = ?',
            (entity_type,)
        )
        count = cursor.fetchone()[0]
        
        if count == 0:
            cursor.execute(
                '''
                INSERT INTO sync_status 
                (entity_type, last_synced_id, last_sync_time) 
                VALUES (?, 0, CURRENT_TIMESTAMP)
                ''',
                (entity_type,)
            )
            
    def close(self) -> None:
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.debug("Database connection closed")
            
    def create_activity_log(self, window_title: str, process_name: str, executable_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new activity log entry.
        
        Args:
            window_title: Title of the active window
            process_name: Name of the process
            executable_path: Path to the executable (optional)
            
        Returns:
            dict: The created activity log
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # End any existing active activity
            self._end_active_activities()
            
            # Create new activity log
            cursor.execute(
                '''
                INSERT INTO activity_logs 
                (window_title, process_name, executable_path) 
                VALUES (?, ?, ?)
                ''',
                (window_title, process_name, executable_path)
            )
            
            # Get the created activity log
            activity_id = cursor.lastrowid
            
            # Commit changes
            self.conn.commit()
            
            # Return the created activity log
            return self.get_activity_log(activity_id)
        except Exception as e:
            logger.error(f"Error creating activity log: {str(e)}")
            self.conn.rollback()
            raise
            
    def end_activity_log(self, activity_id: int) -> Dict[str, Any]:
        """
        End an activity log by setting end_time and calculating duration.
        
        Args:
            activity_id: ID of the activity log to end
            
        Returns:
            dict: The updated activity log
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get the activity to check if it's active
            cursor.execute(
                'SELECT is_active, start_time FROM activity_logs WHERE id = ?',
                (activity_id,)
            )
            activity = cursor.fetchone()
            
            if not activity:
                logger.warning(f"Activity log not found: {activity_id}")
                return {}
                
            is_active, start_time = activity
            
            if not is_active:
                logger.warning(f"Activity log already ended: {activity_id}")
                return self.get_activity_log(activity_id)
                
            # Set end time and calculate duration
            end_time = datetime.now().isoformat()
            
            # Parse start time from string if needed
            if isinstance(start_time, str):
                start_datetime = datetime.fromisoformat(start_time)
            else:
                start_datetime = start_time
                
            # Calculate duration in seconds
            end_datetime = datetime.fromisoformat(end_time)
            duration = (end_datetime - start_datetime).total_seconds()
            
            # Update activity log
            cursor.execute(
                '''
                UPDATE activity_logs 
                SET end_time = ?, duration = ?, is_active = 0, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
                ''',
                (end_time, duration, activity_id)
            )
            
            # Commit changes
            self.conn.commit()
            
            # Return the updated activity log
            return self.get_activity_log(activity_id)
        except Exception as e:
            logger.error(f"Error ending activity log: {str(e)}")
            self.conn.rollback()
            raise
            
    def get_activity_log(self, activity_id: int) -> Dict[str, Any]:
        """
        Get an activity log by ID.
        
        Args:
            activity_id: ID of the activity log to get
            
        Returns:
            dict: The activity log
        """
        try:
            cursor = self.conn.cursor()
            
            # Get the activity log
            cursor.execute(
                '''
                SELECT 
                    id, window_title, process_name, executable_path, 
                    start_time, end_time, duration, is_active, synced,
                    created_at, updated_at
                FROM activity_logs 
                WHERE id = ?
                ''',
                (activity_id,)
            )
            
            activity = cursor.fetchone()
            
            if not activity:
                logger.warning(f"Activity log not found: {activity_id}")
                return {}
                
            # Convert to dictionary
            column_names = [
                'id', 'window_title', 'process_name', 'executable_path',
                'start_time', 'end_time', 'duration', 'is_active', 'synced',
                'created_at', 'updated_at'
            ]
            
            return dict(zip(column_names, activity))
        except Exception as e:
            logger.error(f"Error getting activity log: {str(e)}")
            return {}
            
    def get_active_activity(self) -> Dict[str, Any]:
        """
        Get the currently active activity log.
        
        Returns:
            dict: The active activity log or empty dict if none
        """
        try:
            cursor = self.conn.cursor()
            
            # Get the active activity log
            cursor.execute(
                '''
                SELECT 
                    id, window_title, process_name, executable_path, 
                    start_time, end_time, duration, is_active, synced,
                    created_at, updated_at
                FROM activity_logs 
                WHERE is_active = 1
                '''
            )
            
            activity = cursor.fetchone()
            
            if not activity:
                return {}
                
            # Convert to dictionary
            column_names = [
                'id', 'window_title', 'process_name', 'executable_path',
                'start_time', 'end_time', 'duration', 'is_active', 'synced',
                'created_at', 'updated_at'
            ]
            
            return dict(zip(column_names, activity))
        except Exception as e:
            logger.error(f"Error getting active activity: {str(e)}")
            return {}
            
    def _end_active_activities(self) -> None:
        """End any existing active activity logs."""
        active_activity = self.get_active_activity()
        
        if active_activity:
            self.end_activity_log(active_activity['id'])
            
    def create_screenshot(
        self,
        filepath: str,
        thumbnail_path: Optional[str] = None,
        activity_log_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new screenshot entry.
        
        Args:
            filepath: Path to the screenshot file
            thumbnail_path: Path to the thumbnail (optional)
            activity_log_id: ID of the related activity log (optional)
            
        Returns:
            dict: The created screenshot
        """
        try:
            # If activity_log_id not provided, try to get active activity
            if not activity_log_id:
                active_activity = self.get_active_activity()
                if active_activity:
                    activity_log_id = active_activity['id']
                    
            cursor = self.conn.cursor()
            
            # Create new screenshot
            cursor.execute(
                '''
                INSERT INTO screenshots 
                (filepath, thumbnail_path, activity_log_id) 
                VALUES (?, ?, ?)
                ''',
                (filepath, thumbnail_path, activity_log_id)
            )
            
            # Get the created screenshot
            screenshot_id = cursor.lastrowid
            
            # Commit changes
            self.conn.commit()
            
            # Return the created screenshot
            return self.get_screenshot(screenshot_id)
        except Exception as e:
            logger.error(f"Error creating screenshot: {str(e)}")
            self.conn.rollback()
            raise
            
    def get_screenshot(self, screenshot_id: int) -> Dict[str, Any]:
        """
        Get a screenshot by ID.
        
        Args:
            screenshot_id: ID of the screenshot to get
            
        Returns:
            dict: The screenshot
        """
        try:
            cursor = self.conn.cursor()
            
            # Get the screenshot
            cursor.execute(
                '''
                SELECT 
                    id, filepath, thumbnail_path, activity_log_id, 
                    timestamp, synced, created_at
                FROM screenshots 
                WHERE id = ?
                ''',
                (screenshot_id,)
            )
            
            screenshot = cursor.fetchone()
            
            if not screenshot:
                logger.warning(f"Screenshot not found: {screenshot_id}")
                return {}
                
            # Convert to dictionary
            column_names = [
                'id', 'filepath', 'thumbnail_path', 'activity_log_id',
                'timestamp', 'synced', 'created_at'
            ]
            
            return dict(zip(column_names, screenshot))
        except Exception as e:
            logger.error(f"Error getting screenshot: {str(e)}")
            return {}
            
    def create_system_metric(
        self,
        cpu_percent: float,
        memory_percent: float,
        battery_percent: Optional[float] = None,
        battery_charging: Optional[bool] = None,
        activity_log_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Create a new system metric entry.
        
        Args:
            cpu_percent: CPU usage percentage
            memory_percent: Memory usage percentage
            battery_percent: Battery percentage (optional)
            battery_charging: Whether the battery is charging (optional)
            activity_log_id: ID of the related activity log (optional)
            
        Returns:
            dict: The created system metric
        """
        try:
            # If activity_log_id not provided, try to get active activity
            if not activity_log_id:
                active_activity = self.get_active_activity()
                if active_activity:
                    activity_log_id = active_activity['id']
                    
            cursor = self.conn.cursor()
            
            # Create new system metric
            cursor.execute(
                '''
                INSERT INTO system_metrics 
                (cpu_percent, memory_percent, battery_percent, battery_charging, activity_log_id) 
                VALUES (?, ?, ?, ?, ?)
                ''',
                (cpu_percent, memory_percent, battery_percent, battery_charging, activity_log_id)
            )
            
            # Get the created system metric
            metric_id = cursor.lastrowid
            
            # Commit changes
            self.conn.commit()
            
            # Return the created system metric
            return self.get_system_metric(metric_id)
        except Exception as e:
            logger.error(f"Error creating system metric: {str(e)}")
            self.conn.rollback()
            raise
            
    def get_system_metric(self, metric_id: int) -> Dict[str, Any]:
        """
        Get a system metric by ID.
        
        Args:
            metric_id: ID of the system metric to get
            
        Returns:
            dict: The system metric
        """
        try:
            cursor = self.conn.cursor()
            
            # Get the system metric
            cursor.execute(
                '''
                SELECT 
                    id, cpu_percent, memory_percent, battery_percent, 
                    battery_charging, activity_log_id, timestamp, 
                    synced, created_at
                FROM system_metrics 
                WHERE id = ?
                ''',
                (metric_id,)
            )
            
            metric = cursor.fetchone()
            
            if not metric:
                logger.warning(f"System metric not found: {metric_id}")
                return {}
                
            # Convert to dictionary
            column_names = [
                'id', 'cpu_percent', 'memory_percent', 'battery_percent',
                'battery_charging', 'activity_log_id', 'timestamp',
                'synced', 'created_at'
            ]
            
            return dict(zip(column_names, metric))
        except Exception as e:
            logger.error(f"Error getting system metric: {str(e)}")
            return {}
            
    def get_activity_logs(
        self,
        limit: int = 50,
        offset: int = 0,
        synced: Optional[bool] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get activity logs with optional filtering.
        
        Args:
            limit: Maximum number of logs to return
            offset: Offset for pagination
            synced: Filter by synced status (optional)
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            
        Returns:
            list: List of activity logs
        """
        try:
            cursor = self.conn.cursor()
            
            # Build query
            query = '''
            SELECT 
                id, window_title, process_name, executable_path, 
                start_time, end_time, duration, is_active, synced,
                created_at, updated_at
            FROM activity_logs 
            WHERE 1=1
            '''
            
            params = []
            
            # Add filters
            if synced is not None:
                query += ' AND synced = ?'
                params.append(1 if synced else 0)
                
            if start_date:
                query += ' AND start_time >= ?'
                params.append(start_date)
                
            if end_date:
                query += ' AND start_time <= ?'
                params.append(end_date)
                
            # Add sorting and pagination
            query += ' ORDER BY start_time DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            # Execute query
            cursor.execute(query, params)
            
            # Get results
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            column_names = [
                'id', 'window_title', 'process_name', 'executable_path',
                'start_time', 'end_time', 'duration', 'is_active', 'synced',
                'created_at', 'updated_at'
            ]
            
            return [dict(zip(column_names, row)) for row in results]
        except Exception as e:
            logger.error(f"Error getting activity logs: {str(e)}")
            return []
            
    def get_screenshots(
        self,
        limit: int = 50,
        offset: int = 0,
        synced: Optional[bool] = None,
        activity_log_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get screenshots with optional filtering.
        
        Args:
            limit: Maximum number of screenshots to return
            offset: Offset for pagination
            synced: Filter by synced status (optional)
            activity_log_id: Filter by activity log ID (optional)
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            
        Returns:
            list: List of screenshots
        """
        try:
            cursor = self.conn.cursor()
            
            # Build query
            query = '''
            SELECT 
                id, filepath, thumbnail_path, activity_log_id, 
                timestamp, synced, created_at
            FROM screenshots 
            WHERE 1=1
            '''
            
            params = []
            
            # Add filters
            if synced is not None:
                query += ' AND synced = ?'
                params.append(1 if synced else 0)
                
            if activity_log_id:
                query += ' AND activity_log_id = ?'
                params.append(activity_log_id)
                
            if start_date:
                query += ' AND timestamp >= ?'
                params.append(start_date)
                
            if end_date:
                query += ' AND timestamp <= ?'
                params.append(end_date)
                
            # Add sorting and pagination
            query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            # Execute query
            cursor.execute(query, params)
            
            # Get results
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            column_names = [
                'id', 'filepath', 'thumbnail_path', 'activity_log_id',
                'timestamp', 'synced', 'created_at'
            ]
            
            return [dict(zip(column_names, row)) for row in results]
        except Exception as e:
            logger.error(f"Error getting screenshots: {str(e)}")
            return []
            
    def get_system_metrics(
        self,
        limit: int = 100,
        offset: int = 0,
        synced: Optional[bool] = None,
        activity_log_id: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get system metrics with optional filtering.
        
        Args:
            limit: Maximum number of metrics to return
            offset: Offset for pagination
            synced: Filter by synced status (optional)
            activity_log_id: Filter by activity log ID (optional)
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            
        Returns:
            list: List of system metrics
        """
        try:
            cursor = self.conn.cursor()
            
            # Build query
            query = '''
            SELECT 
                id, cpu_percent, memory_percent, battery_percent, 
                battery_charging, activity_log_id, timestamp, 
                synced, created_at
            FROM system_metrics 
            WHERE 1=1
            '''
            
            params = []
            
            # Add filters
            if synced is not None:
                query += ' AND synced = ?'
                params.append(1 if synced else 0)
                
            if activity_log_id:
                query += ' AND activity_log_id = ?'
                params.append(activity_log_id)
                
            if start_date:
                query += ' AND timestamp >= ?'
                params.append(start_date)
                
            if end_date:
                query += ' AND timestamp <= ?'
                params.append(end_date)
                
            # Add sorting and pagination
            query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
            params.extend([limit, offset])
            
            # Execute query
            cursor.execute(query, params)
            
            # Get results
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            column_names = [
                'id', 'cpu_percent', 'memory_percent', 'battery_percent',
                'battery_charging', 'activity_log_id', 'timestamp',
                'synced', 'created_at'
            ]
            
            return [dict(zip(column_names, row)) for row in results]
        except Exception as e:
            logger.error(f"Error getting system metrics: {str(e)}")
            return []
            
    def mark_synced(self, entity_type: str, entity_id: int) -> bool:
        """
        Mark an entity as synced.
        
        Args:
            entity_type: Type of entity (activity_logs, screenshots, system_metrics)
            entity_id: ID of the entity
            
        Returns:
            bool: True if successful
        """
        try:
            cursor = self.conn.cursor()
            
            # Update the entity
            cursor.execute(
                f'UPDATE {entity_type} SET synced = 1 WHERE id = ?',
                (entity_id,)
            )
            
            # Commit changes
            self.conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error marking {entity_type} {entity_id} as synced: {str(e)}")
            self.conn.rollback()
            return False
            
    def update_sync_status(self, entity_type: str, last_synced_id: int) -> bool:
        """
        Update the sync status for an entity type.
        
        Args:
            entity_type: Type of entity (activity_logs, screenshots, system_metrics)
            last_synced_id: ID of the last synced entity
            
        Returns:
            bool: True if successful
        """
        try:
            cursor = self.conn.cursor()
            
            # Update the sync status
            cursor.execute(
                '''
                UPDATE sync_status 
                SET last_synced_id = ?, last_sync_time = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP 
                WHERE entity_type = ?
                ''',
                (last_synced_id, entity_type)
            )
            
            # Commit changes
            self.conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error updating sync status for {entity_type}: {str(e)}")
            self.conn.rollback()
            return False
            
    def get_sync_status(self, entity_type: str) -> Dict[str, Any]:
        """
        Get the sync status for an entity type.
        
        Args:
            entity_type: Type of entity (activity_logs, screenshots, system_metrics)
            
        Returns:
            dict: The sync status
        """
        try:
            cursor = self.conn.cursor()
            
            # Get the sync status
            cursor.execute(
                '''
                SELECT 
                    id, entity_type, last_synced_id, last_sync_time, 
                    created_at, updated_at
                FROM sync_status 
                WHERE entity_type = ?
                ''',
                (entity_type,)
            )
            
            sync_status = cursor.fetchone()
            
            if not sync_status:
                # Create sync status if it doesn't exist
                self._ensure_sync_status(entity_type)
                
                # Try again
                cursor.execute(
                    '''
                    SELECT 
                        id, entity_type, last_synced_id, last_sync_time, 
                        created_at, updated_at
                    FROM sync_status 
                    WHERE entity_type = ?
                    ''',
                    (entity_type,)
                )
                
                sync_status = cursor.fetchone()
                
            # Convert to dictionary
            column_names = [
                'id', 'entity_type', 'last_synced_id', 'last_sync_time',
                'created_at', 'updated_at'
            ]
            
            return dict(zip(column_names, sync_status))
        except Exception as e:
            logger.error(f"Error getting sync status for {entity_type}: {str(e)}")
            return {
                'entity_type': entity_type,
                'last_synced_id': 0,
                'last_sync_time': datetime.now().isoformat()
            }
            
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            dict: Database statistics
        """
        try:
            cursor = self.conn.cursor()
            
            # Get activity log counts
            cursor.execute('SELECT COUNT(*) FROM activity_logs')
            activity_logs_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM activity_logs WHERE synced = 0')
            activity_logs_unsynced = cursor.fetchone()[0]
            
            # Get screenshot counts
            cursor.execute('SELECT COUNT(*) FROM screenshots')
            screenshots_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM screenshots WHERE synced = 0')
            screenshots_unsynced = cursor.fetchone()[0]
            
            # Get system metric counts
            cursor.execute('SELECT COUNT(*) FROM system_metrics')
            system_metrics_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM system_metrics WHERE synced = 0')
            system_metrics_unsynced = cursor.fetchone()[0]
            
            # Get database file size
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            return {
                'activity_logs_count': activity_logs_count,
                'activity_logs_unsynced': activity_logs_unsynced,
                'screenshots_count': screenshots_count,
                'screenshots_unsynced': screenshots_unsynced,
                'system_metrics_count': system_metrics_count,
                'system_metrics_unsynced': system_metrics_unsynced,
                'database_size': db_size,
                'database_path': self.db_path
            }
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {}
    def execute_query(self, query: str, params: tuple = ()) -> List[Tuple]:
        """
        Execute a raw SQL query.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            list: Query results
        """
        try:
            cursor = self.conn.cursor()
            
            # Execute query
            cursor.execute(query, params)
            
            # Get results
            results = cursor.fetchall()
            
            # Commit if needed
            if query.strip().lower().startswith(('insert', 'update', 'delete')):
                self.conn.commit()
                
            return results
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            self.conn.rollback()
            return []
            
    def get_unsynchronized_activity_logs(self, last_id: int = 0) -> List[Dict[str, Any]]:
        """
        Get unsynchronized activity logs.
        
        Args:
            last_id: ID threshold to filter by
            
        Returns:
            list: List of unsynchronized activity logs
        """
        try:
            cursor = self.conn.cursor()
            
            # Build query
            query = '''
            SELECT 
                id, window_title, process_name, executable_path, 
                start_time, end_time, duration, is_active, synced,
                created_at, updated_at
            FROM activity_logs 
            WHERE synced = 0 AND id > ?
            ORDER BY id ASC
            LIMIT 1000
            '''
            
            # Execute query
            cursor.execute(query, (last_id,))
            
            # Get results
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            column_names = [
                'id', 'window_title', 'process_name', 'executable_path',
                'start_time', 'end_time', 'duration', 'is_active', 'synced',
                'created_at', 'updated_at'
            ]
            
            return [dict(zip(column_names, row)) for row in results]
        except Exception as e:
            logger.error(f"Error getting unsynchronized activity logs: {str(e)}")
            return []
            
    def get_unsynchronized_screenshots(self, last_id: int = 0) -> List[Dict[str, Any]]:
        """
        Get unsynchronized screenshots.
        
        Args:
            last_id: ID threshold to filter by
            
        Returns:
            list: List of unsynchronized screenshots
        """
        try:
            cursor = self.conn.cursor()
            
            # Build query
            query = '''
            SELECT 
                id, filepath, thumbnail_path, activity_log_id, 
                timestamp, synced, created_at
            FROM screenshots 
            WHERE synced = 0 AND id > ?
            ORDER BY id ASC
            LIMIT 500
            '''
            
            # Execute query
            cursor.execute(query, (last_id,))
            
            # Get results
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            column_names = [
                'id', 'filepath', 'thumbnail_path', 'activity_log_id',
                'timestamp', 'synced', 'created_at'
            ]
            
            return [dict(zip(column_names, row)) for row in results]
        except Exception as e:
            logger.error(f"Error getting unsynchronized screenshots: {str(e)}")
            return []
            
    def update_activity_log_sync_status(self, activity_id: int, synced: bool) -> bool:
        """
        Update the sync status of an activity log.
        
        Args:
            activity_id: ID of the activity log
            synced: Sync status to set
            
        Returns:
            bool: True if successful
        """
        return self.mark_synced('activity_logs', activity_id) if synced else False
            
    def update_screenshot_sync_status(self, screenshot_id: int, synced: bool) -> bool:
        """
        Update the sync status of a screenshot.
        
        Args:
            screenshot_id: ID of the screenshot
            synced: Sync status to set
            
        Returns:
            bool: True if successful
        """
        return self.mark_synced('screenshots', screenshot_id) if synced else False
            
    def save_organization_data(self, org_data: Dict[str, Any]) -> bool:
        """
        Save organization data to local database.
        
        Args:
            org_data: Organization data from Supabase
            
        Returns:
            bool: True if successful
        """
        try:
            cursor = self.conn.cursor()
            
            # Check if organization exists
            cursor.execute(
                'SELECT COUNT(*) FROM organizations WHERE id = ?',
                (org_data['id'],)
            )
            
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                # Update existing organization
                cursor.execute(
                    '''
                    UPDATE organizations
                    SET name = ?, settings = ?, updated_at = ?
                    WHERE id = ?
                    ''',
                    (
                        org_data['name'],
                        json.dumps(org_data.get('settings', {})),
                        org_data.get('updated_at') or datetime.now().isoformat(),
                        org_data['id']
                    )
                )
            else:
                # Create new organization
                cursor.execute(
                    '''
                    INSERT INTO organizations
                    (id, name, settings, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (
                        org_data['id'],
                        org_data['name'],
                        json.dumps(org_data.get('settings', {})),
                        org_data.get('created_at') or datetime.now().isoformat(),
                        org_data.get('updated_at') or datetime.now().isoformat()
                    )
                )
                
            # Commit changes
            self.conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error saving organization data: {str(e)}")
            self.conn.rollback()
            return False
            
    def save_org_membership(self, membership_data: Dict[str, Any]) -> bool:
        """
        Save organization membership data to local database.
        
        Args:
            membership_data: Organization membership data from Supabase
            
        Returns:
            bool: True if successful
        """
        try:
            cursor = self.conn.cursor()
            
            # Check if membership exists
            cursor.execute(
                'SELECT COUNT(*) FROM org_members WHERE id = ?',
                (membership_data['id'],)
            )
            
            exists = cursor.fetchone()[0] > 0
            
            if exists:
                # Update existing membership
                cursor.execute(
                    '''
                    UPDATE org_members
                    SET org_id = ?, user_id = ?, role = ?
                    WHERE id = ?
                    ''',
                    (
                        membership_data['org_id'],
                        membership_data['user_id'],
                        membership_data['role'],
                        membership_data['id']
                    )
                )
            else:
                # Create new membership
                cursor.execute(
                    '''
                    INSERT INTO org_members
                    (id, org_id, user_id, role, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    ''',
                    (
                        membership_data['id'],
                        membership_data['org_id'],
                        membership_data['user_id'],
                        membership_data['role'],
                        membership_data.get('created_at') or datetime.now().isoformat()
                    )
                )
                
            # Commit changes
            self.conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error saving organization membership: {str(e)}")
            self.conn.rollback()
            return False
            
    def get_user_org_membership(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get organization membership for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            dict: Organization membership or None if not found
        """
        try:
            cursor = self.conn.cursor()
            
            # Get user's organization membership
            cursor.execute(
                '''
                SELECT 
                    id, org_id, user_id, role, created_at
                FROM org_members
                WHERE user_id = ?
                ''',
                (user_id,)
            )
            
            membership = cursor.fetchone()
            
            if not membership:
                return None
                
            # Convert to dictionary
            column_names = [
                'id', 'org_id', 'user_id', 'role', 'created_at'
            ]
            
            return dict(zip(column_names, membership))
        except Exception as e:
            logger.error(f"Error getting user organization membership: {str(e)}")
            return None

    # Client CRUD operations
    def get_clients(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get clients with pagination.
        
        Args:
            limit: Maximum number of clients to return
            offset: Offset for pagination
            
        Returns:
            list: List of clients
        """
        try:
            cursor = self.conn.cursor()
            
            # Count total clients
            cursor.execute('SELECT COUNT(*) FROM clients')
            total = cursor.fetchone()[0]
            
            # Build query
            query = '''
            SELECT 
                id, name, contact_name, email, phone, address, notes,
                is_active, synced, created_at, updated_at
            FROM clients 
            ORDER BY name ASC
            LIMIT ? OFFSET ?
            '''
            
            # Execute query
            cursor.execute(query, (limit, offset))
            
            # Get results
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            column_names = [
                'id', 'name', 'contact_name', 'email', 'phone', 
                'address', 'notes', 'is_active', 'synced', 
                'created_at', 'updated_at'
            ]
            
            return {
                "total": total,
                "clients": [dict(zip(column_names, row)) for row in results]
            }
        except Exception as e:
            logger.error(f"Error getting clients: {str(e)}")
            return {"total": 0, "clients": []}
            
    def get_client(self, client_id: str) -> Dict[str, Any]:
        """
        Get a client by ID.
        
        Args:
            client_id: ID of the client to get
            
        Returns:
            dict: The client
        """
        try:
            cursor = self.conn.cursor()
            
            # Get the client
            cursor.execute(
                '''
                SELECT 
                    id, name, contact_name, email, phone, address, notes,
                    is_active, synced, created_at, updated_at
                FROM clients 
                WHERE id = ?
                ''',
                (client_id,)
            )
            
            client = cursor.fetchone()
            
            if not client:
                return {}
                
            # Convert to dictionary
            column_names = [
                'id', 'name', 'contact_name', 'email', 'phone', 
                'address', 'notes', 'is_active', 'synced', 
                'created_at', 'updated_at'
            ]
            
            return dict(zip(column_names, client))
        except Exception as e:
            logger.error(f"Error getting client: {str(e)}")
            return {}
            
    def create_client(self, client_data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """
        Create a new client.
        
        Args:
            client_data: Client data
            user_id: ID of the user creating the client
            
        Returns:
            dict: The created client
        """
        try:
            cursor = self.conn.cursor()
            
            # Generate ID and timestamps
            client_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            # Insert client
            cursor.execute(
                '''
                INSERT INTO clients
                (id, name, contact_name, email, phone, address, notes, 
                is_active, created_at, updated_at, user_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    client_id,
                    client_data.get('name', ''),
                    client_data.get('contact_name'),
                    client_data.get('email'),
                    client_data.get('phone'),
                    client_data.get('address'),
                    client_data.get('notes'),
                    1,  # is_active = True
                    now,
                    now,
                    user_id
                )
            )
            
            # Commit changes
            self.conn.commit()
            
            # Return the created client
            return self.get_client(client_id)
        except Exception as e:
            logger.error(f"Error creating client: {str(e)}")
            self.conn.rollback()
            return {}
            
    def update_client(self, client_id: str, client_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a client.
        
        Args:
            client_id: ID of the client to update
            client_data: Client data to update
            
        Returns:
            dict: The updated client
        """
        try:
            cursor = self.conn.cursor()
            
            # Get the client to check if it exists
            client = self.get_client(client_id)
            if not client:
                return {}
                
            # Build update parts
            update_parts = []
            params = []
            
            # Add fields to update
            for field in ['name', 'contact_name', 'email', 'phone', 'address', 'notes', 'is_active']:
                if field in client_data:
                    update_parts.append(f"{field} = ?")
                    params.append(client_data[field])
            
            # Add updated_at timestamp
            update_parts.append("updated_at = ?")
            params.append(datetime.now().isoformat())
            
            # Add client_id to params
            params.append(client_id)
            
            # Execute update
            cursor.execute(
                f'''
                UPDATE clients 
                SET {', '.join(update_parts)}
                WHERE id = ?
                ''',
                tuple(params)
            )
            
            # Commit changes
            self.conn.commit()
            
            # Return the updated client
            return self.get_client(client_id)
        except Exception as e:
            logger.error(f"Error updating client: {str(e)}")
            self.conn.rollback()
            return {}
            
    def delete_client(self, client_id: str) -> bool:
        """
        Delete a client.
        
        Args:
            client_id: ID of the client to delete
            
        Returns:
            bool: True if successful
        """
        try:
            cursor = self.conn.cursor()
            
            # Get the client to check if it exists
            client = self.get_client(client_id)
            if not client:
                return False
                
            # Delete the client
            cursor.execute(
                '''
                DELETE FROM clients 
                WHERE id = ?
                ''',
                (client_id,)
            )
            
            # Commit changes
            self.conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting client: {str(e)}")
            self.conn.rollback()
            return False
