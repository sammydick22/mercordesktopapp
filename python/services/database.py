"""
Database service for managing the local SQLite database.
"""
import os
import sqlite3
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import uuid
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
        
        # For all threads, use thread_local storage
        if not hasattr(self._thread_local, 'conn') or self._thread_local.conn is None:
            # Create a new connection for this thread
            self._thread_local.conn = sqlite3.connect(self.db_path, timeout=20.0)
            # Enable foreign keys
            self._thread_local.conn.execute("PRAGMA foreign_keys = ON")
            # Row factory for better column access
            self._thread_local.conn.row_factory = sqlite3.Row
            logger.debug(f"Created new database connection for thread {current_thread_id}")
            
        return self._thread_local.conn
    
    def _initialize_db(self) -> None:
        """Initialize the database by creating the connection and tables."""
        try:
            # Create database directory if it doesn't exist
            os.makedirs(self.db_dir, exist_ok=True)
            
            # Initialize connection using thread-safe method
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
                id TEXT PRIMARY KEY,
                window_title TEXT NOT NULL,
                process_name TEXT NOT NULL,
                executable_path TEXT,
                start_time TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                duration INTEGER,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                synced BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                dubious_times TEXT
            )
            ''')
            
            # Screenshots table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS screenshots (
                id TEXT PRIMARY KEY,
                filepath TEXT NOT NULL,
                thumbnail_path TEXT NOT NULL,
                activity_log_id TEXT,
                time_entry_id TEXT,
                timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                synced BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (activity_log_id) REFERENCES activity_logs(id)
            )
            ''')
            
            # Ensure columns exist for backward compatibility
            cursor.execute("PRAGMA table_info(screenshots)")
            columns = [column[1] for column in cursor.fetchall()]
            
            # Add time_entry_id if missing
            if "time_entry_id" not in columns:
                try:
                    cursor.execute("ALTER TABLE screenshots ADD COLUMN time_entry_id TEXT")
                    logger.info("Added time_entry_id column to screenshots table in core schema")
                except Exception as e:
                    logger.warning(f"Could not add time_entry_id column: {e}")
            
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
                user_id TEXT NOT NULL,
                synced BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                FOREIGN KEY (client_id) REFERENCES clients(id)
            )
            ''')
            
            # Time entries table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS time_entries (
                id TEXT PRIMARY KEY,
                start_time TIMESTAMP NOT NULL,
                end_time TIMESTAMP,
                duration INTEGER,
                project_id TEXT,
                task_id TEXT,
                description TEXT,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                synced BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                user_id TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
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
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_entries_is_active ON time_entries(is_active)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_entries_synced ON time_entries(synced)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_time_entries_project_id ON time_entries(project_id)')
            
            # Initialize sync status for each entity type if not exists
            self._ensure_sync_status("activity_logs")
            self._ensure_sync_status("screenshots")
            self._ensure_sync_status("system_metrics")
            
            # Commit changes
            conn.commit()
            
            logger.debug("Database tables created")
        except Exception as e:
            logger.error(f"Error creating tables: {str(e)}")
            try:
                conn.rollback()
            except Exception:
                logger.error("Could not rollback transaction - connection may be invalid")
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
        """Close the database connection for the current thread."""
        import threading
        current_thread_id = threading.get_ident()
        
        try:
            # Close thread-local connection if it exists
            if hasattr(self._thread_local, 'conn') and self._thread_local.conn:
                self._thread_local.conn.close()
                self._thread_local.conn = None
                logger.debug(f"Database connection closed for thread {current_thread_id}")
        except Exception as e:
            logger.error(f"Error closing database connection: {str(e)}")
            
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
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # End any existing active activity
            self._end_active_activities()
            
            # Generate UUID for the activity log
            activity_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            # Create new activity log
            cursor.execute(
                '''
                INSERT INTO activity_logs 
                (id, window_title, process_name, executable_path, start_time, created_at, updated_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (activity_id, window_title, process_name, executable_path, now, now, now)
            )
            
            # Commit changes
            conn.commit()
            
            # Return the created activity log
            return self.get_activity_log(activity_id)
        except Exception as e:
            logger.error(f"Error creating activity log: {str(e)}")
            conn.rollback()
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
            try:
                if isinstance(start_time, str):
                    # Handle timezone issues by standardizing the format
                    if 'Z' in start_time:
                        start_time = start_time.replace('Z', '+00:00')
                    start_datetime = datetime.fromisoformat(start_time)
                else:
                    start_datetime = start_time
                    
                # Calculate duration in seconds
                end_datetime = datetime.fromisoformat(end_time)
                duration_seconds = (end_datetime - start_datetime).total_seconds()
                
                # Ensure duration is positive and reasonable
                if duration_seconds < 0:
                    logger.warning(f"Negative duration calculated for activity_id={activity_id}, using absolute value: {duration_seconds}")
                    duration_seconds = abs(duration_seconds)
                
                # Cap unreasonably large durations (>24 hours)
                if duration_seconds > 86400:
                    logger.warning(f"Excessive duration calculated for activity_id={activity_id}, capping at 3600: {duration_seconds}")
                    duration_seconds = 3600  # Cap at 1 hour
                
                # Convert to integer for storage
                duration = int(duration_seconds)
                
            except (ValueError, TypeError) as e:
                # Handle timestamp parsing errors
                logger.error(f"Error calculating duration for activity_id={activity_id}: {str(e)}")
                duration = 300  # Default to 5 minutes on error
            
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
            conn.commit()
            
            # Return the updated activity log
            return self.get_activity_log(activity_id)
        except Exception as e:
            logger.error(f"Error ending activity log: {str(e)}")
            conn.rollback()
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
            cursor = self._get_connection().cursor()
            
            # Get the activity log
            cursor.execute(
                '''
                SELECT 
                    id, window_title, process_name, executable_path, 
                    start_time, end_time, duration, is_active, synced,
                    created_at, updated_at, dubious_times
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
                'created_at', 'updated_at', 'dubious_times'
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
            cursor = self._get_connection().cursor()
            
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
        activity_log_id: Optional[str] = None
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
        conn = self._get_connection()
        try:
            # If activity_log_id not provided, try to get active activity
            if not activity_log_id:
                active_activity = self.get_active_activity()
                if active_activity:
                    activity_log_id = active_activity['id']
                    
            cursor = conn.cursor()
            
            # Generate UUID for the screenshot
            screenshot_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            # Create new screenshot
            cursor.execute(
                '''
                INSERT INTO screenshots 
                (id, filepath, thumbnail_path, activity_log_id, timestamp, created_at) 
                VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (screenshot_id, filepath, thumbnail_path, activity_log_id, now, now)
            )
            
            # Commit changes
            conn.commit()
            
            # Return the created screenshot
            return self.get_screenshot(screenshot_id)
        except Exception as e:
            logger.error(f"Error creating screenshot: {str(e)}")
            conn.rollback()
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
            cursor = self._get_connection().cursor()
            
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
        conn = self._get_connection()
        try:
            # If activity_log_id not provided, try to get active activity
            if not activity_log_id:
                active_activity = self.get_active_activity()
                if active_activity:
                    activity_log_id = active_activity['id']
                    
            cursor = conn.cursor()
            
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
            conn.commit()
            
            # Return the created system metric
            return self.get_system_metric(metric_id)
        except Exception as e:
            logger.error(f"Error creating system metric: {str(e)}")
            conn.rollback()
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
            cursor = self._get_connection().cursor()
            
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
            cursor = self._get_connection().cursor()
            
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
            cursor = self._get_connection().cursor()
            
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
            cursor = self._get_connection().cursor()
            
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
        conn = self._get_connection()
        
        # Retry up to 3 times if database is locked
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                cursor = conn.cursor()
                
                # Update the entity
                cursor.execute(
                    f'UPDATE {entity_type} SET synced = 1 WHERE id = ?',
                    (entity_id,)
                )
                
                # Commit changes
                conn.commit()
                
                return True
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and retry_count < max_retries - 1:
                    retry_count += 1
                    import time
                    wait_time = 0.1 * (2 ** retry_count)  # Exponential backoff
                    logger.warning(f"Database locked, retrying in {wait_time:.2f}s (attempt {retry_count}/{max_retries})")
                    time.sleep(wait_time)
                    
                    # Get a fresh connection
                    self._thread_local.conn = None
                    conn = self._get_connection()
                else:
                    logger.error(f"Error marking {entity_type} {entity_id} as synced: {str(e)}")
                    conn.rollback()
                    return False
            except Exception as e:
                logger.error(f"Error marking {entity_type} {entity_id} as synced: {str(e)}")
                conn.rollback()
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
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
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
            conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error updating sync status for {entity_type}: {str(e)}")
            conn.rollback()
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
            cursor = self._get_connection().cursor()
            
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
            cursor = self._get_connection().cursor()
            
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
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Execute query
            cursor.execute(query, params)
            
            # Get results
            results = cursor.fetchall()
            
            # Commit if needed
            if query.strip().lower().startswith(('insert', 'update', 'delete')):
                conn.commit()
                
            return results
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}")
            conn.rollback()
            return []
            
    def update_activity_log_dubious_times(self, activity_id: str, timestamp: str) -> bool:
        """
        Add a timestamp to the dubious_times array for an activity log.
        
        Args:
            activity_id: ID of the activity log
            timestamp: ISO 8601 formatted timestamp to add
            
        Returns:
            bool: True if successful
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get existing dubious_times
            cursor.execute(
                'SELECT dubious_times FROM activity_logs WHERE id = ?',
                (activity_id,)
            )
            result = cursor.fetchone()
            
            if not result:
                logger.warning(f"Activity log not found: {activity_id}")
                return False
            
            # Parse existing times or create new array
            dubious_times = []
            if result[0]:
                try:
                    dubious_times = json.loads(result[0])
                except json.JSONDecodeError:
                    logger.warning(f"Invalid dubious_times JSON for activity_id={activity_id}, resetting")
            
            # Add new timestamp if it's not already in the array
            if timestamp not in dubious_times:
                dubious_times.append(timestamp)
            
            # Update activity log
            cursor.execute(
                'UPDATE activity_logs SET dubious_times = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?',
                (json.dumps(dubious_times), activity_id)
            )
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error updating activity log dubious times: {str(e)}")
            if 'conn' in locals():
                conn.rollback()
            return False
    
    def get_unsynchronized_activity_logs(self, last_id: int = 0) -> List[Dict[str, Any]]:
        """
        Get unsynchronized activity logs.
        
        Args:
            last_id: ID threshold to filter by
            
        Returns:
            list: List of unsynchronized activity logs
        """
        try:
            cursor = self._get_connection().cursor()
            
            # Build query
            query = '''
            SELECT 
                id, window_title, process_name, executable_path, 
                start_time, end_time, duration, is_active, synced,
                created_at, updated_at, dubious_times
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
                'created_at', 'updated_at', 'dubious_times'
            ]
            
            return [dict(zip(column_names, row)) for row in results]
        except Exception as e:
            logger.error(f"Error getting unsynchronized activity logs: {str(e)}")
            return []
            
    def get_unsynchronized_screenshots(self, last_id: str = None) -> List[Dict[str, Any]]:
        """
        Get unsynchronized screenshots.
        
        Args:
            last_id: UUID of last synced screenshot or None to get all unsynchronized
            
        Returns:
            list: List of unsynchronized screenshots
        """
        try:
            cursor = self._get_connection().cursor()
            
            # Build query that selects all fields including time_entry_id
            logger.info(f"Looking for unsynchronized screenshots (synced=0)")
            query = '''
            SELECT 
                id, filepath, thumbnail_path, activity_log_id, time_entry_id,
                timestamp, synced, created_at
            FROM screenshots 
            WHERE synced = 0
            ORDER BY created_at ASC
            LIMIT 500
            '''
            cursor.execute(query)
            
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
            
    def get_unsynchronized_clients(self, last_id: str = "") -> List[Dict[str, Any]]:
        """
        Get unsynchronized clients.
        
        Args:
            last_id: ID threshold to filter by (optional)
            
        Returns:
            list: List of unsynchronized clients
        """
        try:
            cursor = self._get_connection().cursor()
            
            # Build query conditions
            conditions = ["synced = 0"]
            params = []
            
            if last_id:
                conditions.append("id > ?")
                params.append(last_id)
            
            # Build query
            query = f'''
            SELECT 
                id, name, contact_name, email, phone, address, notes,
                is_active, synced, created_at, updated_at, user_id
            FROM clients 
            WHERE {" AND ".join(conditions)}
            ORDER BY id ASC
            LIMIT 100
            '''
            
            # Execute query
            cursor.execute(query, params)
            
            # Get results
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            column_names = [
                'id', 'name', 'contact_name', 'email', 'phone', 
                'address', 'notes', 'is_active', 'synced', 
                'created_at', 'updated_at', 'user_id'
            ]
            
            return [dict(zip(column_names, row)) for row in results]
        except Exception as e:
            logger.error(f"Error getting unsynchronized clients: {str(e)}")
            return []
            
    def get_unsynchronized_projects(self, last_id: str = "") -> List[Dict[str, Any]]:
        """
        Get unsynchronized projects.
        
        Args:
            last_id: ID threshold to filter by (optional)
            
        Returns:
            list: List of unsynchronized projects
        """
        try:
            cursor = self._get_connection().cursor()
            
            # Build query conditions
            conditions = ["synced = 0"]
            params = []
            
            if last_id:
                conditions.append("id > ?")
                params.append(last_id)
            
            # Build query
            query = f'''
            SELECT 
                id, name, client_id, description, color, 
                hourly_rate, is_billable, is_active, user_id, 
                synced, created_at, updated_at
            FROM projects 
            WHERE {" AND ".join(conditions)}
            ORDER BY id ASC
            LIMIT 100
            '''
            
            # Execute query
            cursor.execute(query, params)
            
            # Get results
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            column_names = [
                'id', 'name', 'client_id', 'description', 'color',
                'hourly_rate', 'is_billable', 'is_active', 'user_id',
                'synced', 'created_at', 'updated_at'
            ]
            
            return [dict(zip(column_names, row)) for row in results]
        except Exception as e:
            logger.error(f"Error getting unsynchronized projects: {str(e)}")
            return []
            
    def get_unsynchronized_time_entries(self, last_id: str = "") -> List[Dict[str, Any]]:
        """
        Get unsynchronized time entries.
        
        Args:
            last_id: ID threshold to filter by (optional)
            
        Returns:
            list: List of unsynchronized time entries
        """
        try:
            cursor = self._get_connection().cursor()
            
            # Build query conditions
            conditions = ["synced = 0"]
            params = []
            
            if last_id:
                conditions.append("id > ?")
                params.append(last_id)
            
            # Build query
            query = f'''
            SELECT 
                id, start_time, end_time, duration, project_id,
                task_id, description, is_active, synced,
                created_at, updated_at, user_id
            FROM time_entries 
            WHERE {" AND ".join(conditions)}
            ORDER BY id ASC
            LIMIT 100
            '''
            
            # Execute query
            cursor.execute(query, params)
            
            # Get results
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            column_names = [
                'id', 'start_time', 'end_time', 'duration', 'project_id',
                'task_id', 'description', 'is_active', 'synced',
                'created_at', 'updated_at', 'user_id'
            ]
            
            return [dict(zip(column_names, row)) for row in results]
        except Exception as e:
            logger.error(f"Error getting unsynchronized time entries: {str(e)}")
            return []
            
    def get_unsynchronized_tasks(self, last_id: str = "") -> List[Dict[str, Any]]:
        """
        Get unsynchronized tasks.
        
        Args:
            last_id: ID threshold to filter by (optional)
            
        Returns:
            list: List of unsynchronized tasks
        """
        try:
            cursor = self._get_connection().cursor()
            
            # Build query conditions
            conditions = ["synced = 0"]
            params = []
            
            if last_id:
                conditions.append("id > ?")
                params.append(last_id)
            
            # Build query
            query = f'''
            SELECT 
                id, name, project_id, description, is_completed,
                due_date, is_active, synced, created_at, updated_at, user_id
            FROM tasks 
            WHERE {" AND ".join(conditions)}
            ORDER BY id ASC
            LIMIT 100
            '''
            
            # Execute query with error handling
            try:
                cursor.execute(query, params)
                
                # Get results
                results = cursor.fetchall()
                
                # Convert to list of dictionaries
                column_names = [
                    'id', 'name', 'project_id', 'description', 'is_completed',
                    'due_date', 'is_active', 'synced', 'created_at', 'updated_at', 'user_id'
                ]
                
                return [dict(zip(column_names, row)) for row in results]
            except sqlite3.OperationalError as e:
                if "no such table: tasks" in str(e):
                    logger.warning("Tasks table doesn't exist yet. Creating it...")
                    self._create_tasks_table()
                    return []
                else:
                    raise
                    
        except Exception as e:
            logger.error(f"Error getting unsynchronized tasks: {str(e)}")
            return []
            
    def _create_tasks_table(self) -> None:
        """Create tasks table if it doesn't exist."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Tasks table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                project_id TEXT,
                description TEXT,
                is_completed BOOLEAN NOT NULL DEFAULT 0,
                due_date TIMESTAMP,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                synced BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL,
                updated_at TIMESTAMP NOT NULL,
                user_id TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )
            ''')
            
            # Create indices
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_project_id ON tasks(project_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_synced ON tasks(synced)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_tasks_user_id ON tasks(user_id)')
            
            # Commit changes
            conn.commit()
            
            logger.info("Tasks table created successfully")
        except Exception as e:
            logger.error(f"Error creating tasks table: {str(e)}")
            conn.rollback()
            raise
            
    def update_task_sync_status(self, task_id: str, synced: bool) -> bool:
        """
        Update the sync status of a task.
        
        Args:
            task_id: ID of the task
            synced: Sync status to set
            
        Returns:
            bool: True if successful
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Update the task sync status
            cursor.execute(
                'UPDATE tasks SET synced = ? WHERE id = ?',
                (1 if synced else 0, task_id)
            )
            
            # Commit changes
            conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error updating task sync status: {str(e)}")
            conn.rollback()
            return False
            
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
        
    def update_client_sync_status(self, client_id: str, synced: bool) -> bool:
        """
        Update the sync status of a client.
        
        Args:
            client_id: ID of the client
            synced: Sync status to set
            
        Returns:
            bool: True if successful
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Update the client sync status
            cursor.execute(
                'UPDATE clients SET synced = ? WHERE id = ?',
                (1 if synced else 0, client_id)
            )
            
            # Commit changes
            conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error updating client sync status: {str(e)}")
            conn.rollback()
            return False
            
    def update_project_sync_status(self, project_id: str, synced: bool) -> bool:
        """
        Update the sync status of a project.
        
        Args:
            project_id: ID of the project
            synced: Sync status to set
            
        Returns:
            bool: True if successful
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Update the project sync status
            cursor.execute(
                'UPDATE projects SET synced = ? WHERE id = ?',
                (1 if synced else 0, project_id)
            )
            
            # Commit changes
            conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error updating project sync status: {str(e)}")
            conn.rollback()
            return False
            
    def update_time_entry_sync_status(self, time_entry_id: str, synced: bool) -> bool:
        """
        Update the sync status of a time entry.
        
        Args:
            time_entry_id: ID of the time entry
            synced: Sync status to set
            
        Returns:
            bool: True if successful
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Update the time entry sync status
            cursor.execute(
                'UPDATE time_entries SET synced = ? WHERE id = ?',
                (1 if synced else 0, time_entry_id)
            )
            
            # Commit changes
            conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error updating time entry sync status: {str(e)}")
            conn.rollback()
            return False
            
    def save_organization_data(self, org_data: Dict[str, Any]) -> bool:
        """
        Save organization data to local database.
        
        Args:
            org_data: Organization data from Supabase
            
        Returns:
            bool: True if successful
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
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
            conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error saving organization data: {str(e)}")
            conn.rollback()
            return False
            
    def save_org_membership(self, membership_data: Dict[str, Any]) -> bool:
        """
        Save organization membership data to local database.
        
        Args:
            membership_data: Organization membership data from Supabase
            
        Returns:
            bool: True if successful
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Log membership data
            logger.info(f"Processing membership data: {json.dumps(membership_data)}")
            
            # Validate required fields
            required_fields = ['id', 'org_id', 'user_id', 'role']
            for field in required_fields:
                if field not in membership_data or not membership_data[field]:
                    logger.error(f"Missing required field '{field}' in membership data")
                    return False
            
            # Verify that the referenced organization exists in the database
            cursor.execute(
                'SELECT COUNT(*) FROM organizations WHERE id = ?',
                (membership_data['org_id'],)
            )
            org_exists = cursor.fetchone()[0] > 0
            
            if not org_exists:
                logger.error(f"Cannot save membership: Organization with ID '{membership_data['org_id']}' does not exist in local database")
                # Dump diagnostic info
                cursor.execute('SELECT id, name FROM organizations')
                orgs = cursor.fetchall()
                logger.debug(f"Available organizations in database: {orgs}")
                return False
            
            # Check if membership exists
            cursor.execute(
                'SELECT COUNT(*) FROM org_members WHERE id = ?',
                (membership_data['id'],)
            )
            
            exists = cursor.fetchone()[0] > 0
            logger.debug(f"Membership record exists: {exists}")
            
            if exists:
                # Update existing membership
                logger.info(f"Updating existing membership for organization '{membership_data['org_id']}'")
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
                logger.info(f"Creating new membership for organization '{membership_data['org_id']}'")
                
                # Double check for duplicate org_id/user_id combo before inserting
                cursor.execute(
                    'SELECT COUNT(*) FROM org_members WHERE org_id = ? AND user_id = ?',
                    (membership_data['org_id'], membership_data['user_id'])
                )
                duplicate_exists = cursor.fetchone()[0] > 0
                
                if duplicate_exists:
                    logger.warning(f"Membership for org '{membership_data['org_id']}' and user '{membership_data['user_id']}' already exists. Skipping.")
                    return True
                
                # Insert the new membership
                try:
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
                except sqlite3.IntegrityError as ie:
                    # Detailed logging for integrity errors
                    error_msg = str(ie)
                    logger.error(f"Database integrity error: {error_msg}")
                    
                    if "FOREIGN KEY constraint failed" in error_msg:
                        # Check which constraint specifically failed
                        logger.error(f"Foreign key constraint failed for membership: org_id={membership_data['org_id']}, user_id={membership_data['user_id']}")
                        
                        # Verify organization existence one more time
                        cursor.execute('SELECT * FROM organizations WHERE id = ?', (membership_data['org_id'],))
                        org = cursor.fetchone()
                        if org:
                            logger.info(f"Organization exists: {org}")
                        else:
                            logger.error(f"Organization with ID '{membership_data['org_id']}' definitely does not exist")
                    
                    conn.rollback()
                    return False
                
            # Commit changes
            conn.commit()
            logger.info(f"Successfully saved membership for org '{membership_data['org_id']}', user '{membership_data['user_id']}'")
            
            return True
        except Exception as e:
            logger.error(f"Error saving organization membership: {str(e)}")
            logger.error(f"Membership data: {json.dumps(membership_data)}")
            conn.rollback()
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
            cursor = self._get_connection().cursor()
            
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
            
    def get_user_org_memberships(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all organization memberships for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            list: List of organization memberships
        """
        try:
            cursor = self._get_connection().cursor()
            
            # Get all user's organization memberships
            cursor.execute(
                '''
                SELECT 
                    id, org_id, user_id, role, created_at
                FROM org_members
                WHERE user_id = ?
                ''',
                (user_id,)
            )
            
            memberships = cursor.fetchall()
            
            if not memberships:
                return []
                
            # Convert to list of dictionaries
            column_names = [
                'id', 'org_id', 'user_id', 'role', 'created_at'
            ]
            
            return [dict(zip(column_names, membership)) for membership in memberships]
        except Exception as e:
            logger.error(f"Error getting user organization memberships: {str(e)}")
            return []
            
    def cleanup_orphaned_memberships(self) -> Dict[str, Any]:
        """
        Clean up orphaned organization memberships that reference non-existent organizations.
        
        Returns:
            dict: Cleanup results with counts
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Find orphaned memberships
            cursor.execute(
                '''
                SELECT om.id, om.org_id, om.user_id
                FROM org_members om
                LEFT JOIN organizations o ON om.org_id = o.id
                WHERE o.id IS NULL
                '''
            )
            
            orphaned_memberships = cursor.fetchall()
            orphaned_count = len(orphaned_memberships)
            
            # Log orphaned memberships before deletion for diagnostic purposes
            if orphaned_count > 0:
                logger.warning(f"Found {orphaned_count} orphaned memberships referencing non-existent organizations")
                for membership in orphaned_memberships:
                    logger.warning(f"Orphaned membership: id={membership[0]}, org_id={membership[1]}, user_id={membership[2]}")
                
                # Delete orphaned memberships
                cursor.execute(
                    '''
                    DELETE FROM org_members
                    WHERE id IN (
                        SELECT om.id
                        FROM org_members om
                        LEFT JOIN organizations o ON om.org_id = o.id
                        WHERE o.id IS NULL
                    )
                    '''
                )
                
                conn.commit()
                logger.info(f"Successfully cleaned up {orphaned_count} orphaned memberships")
            else:
                logger.info("No orphaned memberships found")
            
            return {
                "orphaned_count": orphaned_count,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up orphaned memberships: {str(e)}")
            conn.rollback()
            
            return {
                "orphaned_count": 0,
                "success": False,
                "error": str(e)
            }
            
    def remove_specific_membership(self, org_id: str) -> bool:
        """
        Remove a specific membership by organization ID.
        
        Args:
            org_id: Organization ID to remove memberships for
            
        Returns:
            bool: True if successful
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Find memberships for the organization
            cursor.execute(
                '''
                SELECT id, user_id FROM org_members
                WHERE org_id = ?
                ''',
                (org_id,)
            )
            
            memberships = cursor.fetchall()
            
            if not memberships:
                logger.info(f"No memberships found for organization: {org_id}")
                return True
                
            # Log memberships before deletion
            for membership in memberships:
                logger.warning(f"Removing membership: id={membership[0]}, org_id={org_id}, user_id={membership[1]}")
            
            # Delete memberships
            cursor.execute(
                '''
                DELETE FROM org_members
                WHERE org_id = ?
                ''',
                (org_id,)
            )
            
            conn.commit()
            logger.info(f"Successfully removed {len(memberships)} memberships for organization: {org_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error removing membership for organization {org_id}: {str(e)}")
            conn.rollback()
            return False

    # Client CRUD operations
    def get_clients(self, limit: int = 50, offset: int = 0, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get clients with pagination.
        
        Args:
            limit: Maximum number of clients to return
            offset: Offset for pagination
            user_id: Filter by user ID
            
        Returns:
            list: List of clients
        """
        try:
            cursor = self._get_connection().cursor()
            
            # Build base query conditions
            conditions = []
            params = []
            
            if user_id:
                conditions.append('user_id = ?')
                params.append(user_id)
            
            # Build WHERE clause
            where_clause = ' AND '.join(conditions) if conditions else '1=1'
            
            # Count total clients with filter
            count_query = f'SELECT COUNT(*) FROM clients WHERE {where_clause}'
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
            # Build query
            query = f'''
            SELECT 
                id, name, contact_name, email, phone, address, notes,
                is_active, synced, created_at, updated_at, user_id
            FROM clients 
            WHERE {where_clause}
            ORDER BY name ASC
            LIMIT ? OFFSET ?
            '''
            
            # Add limit and offset to params
            params.extend([limit, offset])
            
            # Execute query
            cursor.execute(query, params)
            
            # Get results
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            column_names = [
                'id', 'name', 'contact_name', 'email', 'phone', 
                'address', 'notes', 'is_active', 'synced', 
                'created_at', 'updated_at', 'user_id'
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
            cursor = self._get_connection().cursor()
            
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
            
    def create_client(self, name: str, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        Create a new client.
        
        Args:
            name: Name of the client
            user_id: ID of the user creating the client
            **kwargs: Additional client data (contact_name, email, phone, address, notes)
            
        Returns:
            dict: The created client
        """
        conn = self._get_connection()
        
        # Retry up to 3 times if database is locked
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                cursor = conn.cursor()
                
                # Generate ID and timestamps
                client_id = str(uuid.uuid4())
                now = datetime.now().isoformat()
                
                # Extract known fields from kwargs
                contact_name = kwargs.get('contact_name')
                email = kwargs.get('email')
                phone = kwargs.get('phone')
                address = kwargs.get('address')
                notes = kwargs.get('notes')
                is_active = kwargs.get('is_active', 1)  # Default to active
                
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
                        name,
                        contact_name,
                        email,
                        phone,
                        address,
                        notes,
                        is_active,
                        now,
                        now,
                        user_id
                    )
                )
                
                # Commit changes
                conn.commit()
                
                # Return the created client
                return self.get_client(client_id)
                
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e) and retry_count < max_retries - 1:
                    retry_count += 1
                    import time
                    wait_time = 0.1 * (2 ** retry_count)  # Exponential backoff
                    logger.warning(f"Database locked, retrying in {wait_time:.2f}s (attempt {retry_count}/{max_retries})")
                    time.sleep(wait_time)
                    
                    # Get a fresh connection
                    self._thread_local.conn = None
                    conn = self._get_connection()
                else:
                    logger.error(f"Error creating client: {str(e)}")
                    conn.rollback()
                    return {}
            except Exception as e:
                logger.error(f"Error creating client: {str(e)}")
                conn.rollback()
                return {}
                
        # If we get here, all retries failed
        logger.error(f"Failed to create client after {max_retries} attempts due to database locks")
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
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
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
            conn.commit()
            
            # Return the updated client
            return self.get_client(client_id)
        except Exception as e:
            logger.error(f"Error updating client: {str(e)}")
            conn.rollback()
            return {}
            
    def delete_client(self, client_id: str) -> bool:
        """
        Delete a client.
        
        Args:
            client_id: ID of the client to delete
            
        Returns:
            bool: True if successful
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
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
            conn.commit()
            
            return True
        except Exception as e:
            logger.error(f"Error deleting client: {str(e)}")
            conn.rollback()
            return False
            
    # Time entries CRUD operations
    def create_time_entry(
        self, 
        user_id: str, 
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new time entry.
        
        Args:
            user_id: ID of the user creating the time entry
            project_id: ID of the project (optional)
            task_id: ID of the task (optional)
            description: Description of the time entry (optional)
            
        Returns:
            dict: The created time entry
        """
        conn = self._get_connection()
        try:
            # End any active time entry first
            self.end_active_time_entries(user_id)
            
            cursor = conn.cursor()
            
            # Generate ID and timestamps
            time_entry_id = str(uuid.uuid4())
            now = datetime.now().isoformat()
            
            # Insert time entry
            cursor.execute(
                '''
                INSERT INTO time_entries
                (id, start_time, project_id, task_id, description, is_active, user_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    time_entry_id,
                    now,
                    project_id,
                    task_id,
                    description,
                    1,  # is_active = True
                    user_id,
                    now,
                    now
                )
            )
            
            # Commit changes
            conn.commit()
            
            # Return the created time entry
            return self.get_time_entry(time_entry_id)
        except Exception as e:
            logger.error(f"Error creating time entry: {str(e)}")
            conn.rollback()
            return {}
            
    def get_time_entry(self, time_entry_id: str) -> Dict[str, Any]:
        """
        Get a time entry by ID.
        
        Args:
            time_entry_id: ID of the time entry to get
            
        Returns:
            dict: The time entry
        """
        try:
            cursor = self._get_connection().cursor()
            
            # Get the time entry
            cursor.execute(
                '''
                SELECT 
                    id, start_time, end_time, duration, project_id, 
                    task_id, description, is_active, synced, 
                    created_at, updated_at, user_id
                FROM time_entries 
                WHERE id = ?
                ''',
                (time_entry_id,)
            )
            
            time_entry = cursor.fetchone()
            
            if not time_entry:
                logger.warning(f"Time entry not found: {time_entry_id}")
                return {}
                
            # Convert to dictionary
            column_names = [
                'id', 'start_time', 'end_time', 'duration', 'project_id',
                'task_id', 'description', 'is_active', 'synced',
                'created_at', 'updated_at', 'user_id'
            ]
            
            return dict(zip(column_names, time_entry))
        except Exception as e:
            logger.error(f"Error getting time entry: {str(e)}")
            return {}
            
    def get_active_time_entry(self, user_id: str) -> Dict[str, Any]:
        """
        Get the currently active time entry for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            dict: The active time entry or empty dict if none
        """
        try:
            cursor = self._get_connection().cursor()
            
            # Get the active time entry
            cursor.execute(
                '''
                SELECT 
                    id, start_time, end_time, duration, project_id, 
                    task_id, description, is_active, synced, 
                    created_at, updated_at, user_id
                FROM time_entries 
                WHERE user_id = ? AND is_active = 1
                ''',
                (user_id,)
            )
            
            time_entry = cursor.fetchone()
            
            if not time_entry:
                return {}
                
            # Convert to dictionary
            column_names = [
                'id', 'start_time', 'end_time', 'duration', 'project_id',
                'task_id', 'description', 'is_active', 'synced',
                'created_at', 'updated_at', 'user_id'
            ]
            
            return dict(zip(column_names, time_entry))
        except Exception as e:
            logger.error(f"Error getting active time entry: {str(e)}")
            return {}
            
    def end_time_entry(self, time_entry_id: str, description: Optional[str] = None) -> Dict[str, Any]:
        """
        End a time entry by setting end_time and calculating duration.
        
        Args:
            time_entry_id: ID of the time entry to end
            description: Optional description to update
            
        Returns:
            dict: The updated time entry
        """
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            
            # Get the time entry to check if it's active
            time_entry = self.get_time_entry(time_entry_id)
            if not time_entry:
                logger.warning(f"Time entry not found: {time_entry_id}")
                return {}
                
            if not time_entry.get('is_active'):
                logger.warning(f"Time entry already ended: {time_entry_id}")
                return time_entry
                
            # Set end time and calculate duration
            now = datetime.now().isoformat()
            
            # Parse start time from string if needed
            start_time = time_entry['start_time']
            if isinstance(start_time, str):
                start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            else:
                start_datetime = start_time
                
            # Calculate duration in seconds
            end_datetime = datetime.fromisoformat(now.replace('Z', '+00:00'))
            duration = int((end_datetime - start_datetime).total_seconds())
            
            # Update time entry
            update_parts = [
                "end_time = ?",
                "duration = ?",
                "is_active = 0",
                "updated_at = ?"
            ]
            params = [now, duration, now]
            
            # Add description if provided
            if description is not None:
                update_parts.append("description = ?")
                params.append(description)
                
            # Add time_entry_id to params
            params.append(time_entry_id)
            
            # Execute update
            cursor.execute(
                f'''
                UPDATE time_entries 
                SET {', '.join(update_parts)}
                WHERE id = ?
                ''',
                tuple(params)
            )
            
            # Commit changes
            conn.commit()
            
            # Return the updated time entry
            return self.get_time_entry(time_entry_id)
        except Exception as e:
            logger.error(f"Error ending time entry: {str(e)}")
            conn.rollback()
            return {}
            
    def end_active_time_entries(self, user_id: str) -> bool:
        """
        End any active time entries for a user.
        
        Args:
            user_id: ID of the user
            
        Returns:
            bool: True if successful
        """
        try:
            active_entry = self.get_active_time_entry(user_id)
            if active_entry:
                self.end_time_entry(active_entry['id'])
            return True
        except Exception as e:
            logger.error(f"Error ending active time entries: {str(e)}")
            return False
            
    def get_time_entries(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        project_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get time entries with pagination and optional filtering.
        
        Args:
            user_id: ID of the user
            limit: Maximum number of entries to return
            offset: Offset for pagination
            project_id: Filter by project ID (optional)
            start_date: Start date for filtering (optional)
            end_date: End date for filtering (optional)
            
        Returns:
            dict: Dictionary with total count and list of time entries
        """
        try:
            cursor = self._get_connection().cursor()
            
            # Build base query conditions
            conditions = ["user_id = ?"]
            params = [user_id]
            
            if project_id:
                conditions.append("project_id = ?")
                params.append(project_id)
                
            if start_date:
                conditions.append("start_time >= ?")
                params.append(start_date)
                
            if end_date:
                conditions.append("start_time <= ?")
                params.append(end_date)
                
            # Build WHERE clause
            where_clause = " AND ".join(conditions)
            
            # Count total time entries with filter
            count_query = f'SELECT COUNT(*) FROM time_entries WHERE {where_clause}'
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
            # Build query
            query = f'''
            SELECT 
                id, start_time, end_time, duration, project_id, 
                task_id, description, is_active, synced, 
                created_at, updated_at, user_id
            FROM time_entries 
            WHERE {where_clause}
            ORDER BY start_time DESC
            LIMIT ? OFFSET ?
            '''
            
            # Add limit and offset to params
            params.extend([limit, offset])
            
            # Execute query
            cursor.execute(query, params)
            
            # Get results
            results = cursor.fetchall()
            
            # Convert to list of dictionaries
            column_names = [
                'id', 'start_time', 'end_time', 'duration', 'project_id',
                'task_id', 'description', 'is_active', 'synced',
                'created_at', 'updated_at', 'user_id'
            ]
            
            return {
                "total": total,
                "time_entries": [dict(zip(column_names, row)) for row in results]
            }
        except Exception as e:
            logger.error(f"Error getting time entries: {str(e)}")
            return {"total": 0, "time_entries": []}
