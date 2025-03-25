"""
Extensions for the DatabaseService to support project, client, and task synchronization.
"""
import logging
from typing import Dict, Any, List, Optional

# Setup logger
logger = logging.getLogger(__name__)

def get_unsynchronized_projects(self, last_id: str = '') -> List[Dict[str, Any]]:
    """
    Get unsynchronized projects.
    
    Args:
        last_id: ID threshold to filter by
        
    Returns:
        list: List of unsynchronized projects
    """
    try:
        cursor = self._get_connection().cursor()
        
        # Build query
        query = '''
        SELECT 
            id, name, client_id, description, color, 
            hourly_rate, is_billable, is_active, user_id,
            created_at, updated_at
        FROM projects 
        WHERE synced = 0 AND id > ?
        ORDER BY id ASC
        LIMIT 100
        '''
        
        # Execute query
        cursor.execute(query, (last_id,))
        
        # Get results
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        column_names = [
            'id', 'name', 'client_id', 'description', 'color',
            'hourly_rate', 'is_billable', 'is_active', 'user_id',
            'created_at', 'updated_at'
        ]
        
        return [dict(zip(column_names, row)) for row in results]
    except Exception as e:
        logger.error(f"Error getting unsynchronized projects: {str(e)}")
        return []

def get_unsynchronized_clients(self, last_id: str = '') -> List[Dict[str, Any]]:
    """
    Get unsynchronized clients.
    
    Args:
        last_id: ID threshold to filter by
        
    Returns:
        list: List of unsynchronized clients
    """
    try:
        cursor = self._get_connection().cursor()
        
        # Build query
        query = '''
        SELECT 
            id, name, contact_name, email, phone, 
            address, notes, is_active, user_id,
            created_at, updated_at
        FROM clients 
        WHERE synced = 0 AND id > ?
        ORDER BY id ASC
        LIMIT 100
        '''
        
        # Execute query
        cursor.execute(query, (last_id,))
        
        # Get results
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        column_names = [
            'id', 'name', 'contact_name', 'email', 'phone',
            'address', 'notes', 'is_active', 'user_id',
            'created_at', 'updated_at'
        ]
        
        return [dict(zip(column_names, row)) for row in results]
    except Exception as e:
        logger.error(f"Error getting unsynchronized clients: {str(e)}")
        return []

def get_project_tasks(self, project_id: str) -> List[Dict[str, Any]]:
    """
    Get tasks for a specific project.
    
    Args:
        project_id: ID of the project
        
    Returns:
        list: List of tasks
    """
    try:
        cursor = self._get_connection().cursor()
        
        # Build query
        query = '''
        SELECT 
            id, name, description, project_id, 
            estimated_hours, is_active, created_at, updated_at
        FROM project_tasks 
        WHERE project_id = ?
        ORDER BY name ASC
        '''
        
        # Execute query
        cursor.execute(query, (project_id,))
        
        # Get results
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        column_names = [
            'id', 'name', 'description', 'project_id',
            'estimated_hours', 'is_active', 'created_at', 'updated_at'
        ]
        
        return [dict(zip(column_names, row)) for row in results]
    except Exception as e:
        logger.error(f"Error getting project tasks: {str(e)}")
        return []

def update_project_sync_status(self, project_id: str, synced: bool) -> bool:
    """
    Update the sync status of a project.
    
    Args:
        project_id: ID of the project
        synced: Sync status to set
        
    Returns:
        bool: True if successful
    """
    try:
        cursor = self._get_connection().cursor()
        
        # Update the project
        cursor.execute(
            'UPDATE projects SET synced = ? WHERE id = ?',
            (1 if synced else 0, project_id)
        )
        
        # Commit changes
        self._get_connection().commit()
        
        return True
    except Exception as e:
        logger.error(f"Error updating project sync status: {str(e)}")
        self._get_connection().rollback()
        return False

def update_client_sync_status(self, client_id: str, synced: bool) -> bool:
    """
    Update the sync status of a client.
    
    Args:
        client_id: ID of the client
        synced: Sync status to set
        
    Returns:
        bool: True if successful
    """
    try:
        cursor = self._get_connection().cursor()
        
        # Update the client
        cursor.execute(
            'UPDATE clients SET synced = ? WHERE id = ?',
            (1 if synced else 0, client_id)
        )
        
        # Commit changes
        self._get_connection().commit()
        
        return True
    except Exception as e:
        logger.error(f"Error updating client sync status: {str(e)}")
        self._get_connection().rollback()
        return False

def get_unsynchronized_user_profiles(self, last_id: str = '') -> List[Dict[str, Any]]:
    """
    Get unsynchronized user profiles.
    
    Args:
        last_id: ID threshold to filter by
        
    Returns:
        list: List of unsynchronized user profiles
    """
    try:
        cursor = self._get_connection().cursor()
        
        # Query for user_profiles table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_profiles'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            logger.warning("user_profiles table does not exist in local database")
            return []
        
        # Check if 'synced' column exists
        try:
            cursor.execute("PRAGMA table_info(user_profiles)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'synced' not in column_names:
                logger.warning("'synced' column does not exist in user_profiles table")
                # Add synced column if it doesn't exist
                try:
                    cursor.execute("ALTER TABLE user_profiles ADD COLUMN synced INTEGER DEFAULT 0")
                    self._get_connection().commit()
                    logger.info("Added 'synced' column to user_profiles table")
                except Exception as add_error:
                    logger.error(f"Error adding 'synced' column: {str(add_error)}")
                    return []
        except Exception as col_error:
            logger.error(f"Error checking columns: {str(col_error)}")
            return []
            
        # Get column names from the actual table
        cursor.execute("PRAGMA table_info(user_profiles)")
        columns = cursor.fetchall()
        actual_columns = [col[1] for col in columns]
        
        # Create a SQL query based on the actual columns
        id_column = 'id' if 'id' in actual_columns else 'user_id'
        name_column = 'full_name' if 'full_name' in actual_columns else ('display_name' if 'display_name' in actual_columns else 'name')
        
        # Build a dynamic query based on available columns
        query_columns = ', '.join(actual_columns)
        
        # Build query
        query = f'''
        SELECT {query_columns}
        FROM user_profiles 
        WHERE synced = 0 AND {id_column} > ?
        ORDER BY {id_column} ASC
        LIMIT 100
        '''
        
        # Execute query
        cursor.execute(query, (last_id,))
        
        # Get results
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        return [dict(zip(actual_columns, row)) for row in results]
    except Exception as e:
        logger.error(f"Error getting unsynchronized user profiles: {str(e)}")
        return []

def get_unsynchronized_user_settings(self, last_id: str = '') -> List[Dict[str, Any]]:
    """
    Get unsynchronized user settings.
    
    Args:
        last_id: ID threshold to filter by
        
    Returns:
        list: List of unsynchronized user settings
    """
    try:
        cursor = self._get_connection().cursor()
        
        # Query for user_settings table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            logger.warning("user_settings table does not exist in local database")
            return []
        
        # Check if 'synced' column exists
        try:
            cursor.execute("PRAGMA table_info(user_settings)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'synced' not in column_names:
                logger.warning("'synced' column does not exist in user_settings table")
                # Add synced column if it doesn't exist
                try:
                    cursor.execute("ALTER TABLE user_settings ADD COLUMN synced INTEGER DEFAULT 0")
                    self._get_connection().commit()
                    logger.info("Added 'synced' column to user_settings table")
                except Exception as add_error:
                    logger.error(f"Error adding 'synced' column: {str(add_error)}")
                    return []
        except Exception as col_error:
            logger.error(f"Error checking columns: {str(col_error)}")
            return []
            
        # Get column names from the actual table
        cursor.execute("PRAGMA table_info(user_settings)")
        columns = cursor.fetchall()
        actual_columns = [col[1] for col in columns]
        
        # Determine the ID column - Supabase uses user_id as primary key
        id_column = 'user_id' 
        
        # Build a dynamic query based on available columns
        query_columns = ', '.join(actual_columns)
        
        # Build query
        query = f'''
        SELECT {query_columns}
        FROM user_settings 
        WHERE synced = 0 AND {id_column} > ?
        ORDER BY {id_column} ASC
        LIMIT 100
        '''
        
        # Execute query
        cursor.execute(query, (last_id,))
        
        # Get results
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        return [dict(zip(actual_columns, row)) for row in results]
    except Exception as e:
        logger.error(f"Error getting unsynchronized user settings: {str(e)}")
        return []

def get_unsynchronized_project_tasks(self, last_id: str = '') -> List[Dict[str, Any]]:
    """
    Get unsynchronized project tasks.
    
    Args:
        last_id: ID threshold to filter by
        
    Returns:
        list: List of unsynchronized project tasks
    """
    try:
        cursor = self._get_connection().cursor()
        
        # Query for project_tasks table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='project_tasks'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            logger.warning("project_tasks table does not exist in local database")
            return []
        
        # Build query
        query = '''
        SELECT 
            id, name, description, project_id, estimated_hours,
            is_active, synced, created_at, updated_at
        FROM project_tasks 
        WHERE synced = 0 AND id > ?
        ORDER BY id ASC
        LIMIT 100
        '''
        
        # Execute query
        cursor.execute(query, (last_id,))
        
        # Get results
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        column_names = [
            'id', 'name', 'description', 'project_id', 'estimated_hours',
            'is_active', 'synced', 'created_at', 'updated_at'
        ]
        
        return [dict(zip(column_names, row)) for row in results]
    except Exception as e:
        logger.error(f"Error getting unsynchronized project tasks: {str(e)}")
        return []
        
def update_user_profile_sync_status(self, profile_id: str, synced: bool) -> bool:
    """
    Update the sync status of a user profile.
    
    Args:
        profile_id: ID of the user profile
        synced: Sync status to set
        
    Returns:
        bool: True if successful
    """
    try:
        cursor = self._get_connection().cursor()
        
        # First check which primary key column exists in the table
        cursor.execute("PRAGMA table_info(user_profiles)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Determine primary key column
        pk_column = None
        if "id" in column_names:
            pk_column = "id"
        elif "user_id" in column_names:
            pk_column = "user_id"
        else:
            raise ValueError("Cannot determine primary key column for user_profiles table")
        
        # Update the user profile
        cursor.execute(
            f'UPDATE user_profiles SET synced = ? WHERE {pk_column} = ?',
            (1 if synced else 0, profile_id)
        )
        
        # Commit changes
        self._get_connection().commit()
        
        return True
    except Exception as e:
        logger.error(f"Error updating user profile sync status: {str(e)}")
        self._get_connection().rollback()
        return False

def update_user_setting_sync_status(self, setting_id: str, synced: bool) -> bool:
    """
    Update the sync status of a user setting.
    
    Args:
        setting_id: ID of the user setting (user_id in Supabase)
        synced: Sync status to set
        
    Returns:
        bool: True if successful
    """
    try:
        cursor = self._get_connection().cursor()
        
        # First check which primary key column exists in the table
        cursor.execute("PRAGMA table_info(user_settings)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Determine primary key column - in Supabase this is user_id
        if "user_id" in column_names:
            # Update the user setting using user_id
            cursor.execute(
                'UPDATE user_settings SET synced = ? WHERE user_id = ?',
                (1 if synced else 0, setting_id)
            )
        elif "id" in column_names:
            # Fallback to id if user_id doesn't exist
            cursor.execute(
                'UPDATE user_settings SET synced = ? WHERE id = ?',
                (1 if synced else 0, setting_id)
            )
        else:
            raise ValueError("Cannot find user_id or id column in user_settings table")
        
        # Commit changes
        self._get_connection().commit()
        
        return True
    except Exception as e:
        logger.error(f"Error updating user setting sync status: {str(e)}")
        self._get_connection().rollback()
        return False
        
def update_project_task_sync_status(self, task_id: str, synced: bool) -> bool:
    """
    Update the sync status of a project task.
    
    Args:
        task_id: ID of the project task
        synced: Sync status to set
        
    Returns:
        bool: True if successful
    """
    try:
        cursor = self._get_connection().cursor()
        
        # Update the project task
        cursor.execute(
            'UPDATE project_tasks SET synced = ? WHERE id = ?',
            (1 if synced else 0, task_id)
        )
        
        # Commit changes
        self._get_connection().commit()
        
        return True
    except Exception as e:
        logger.error(f"Error updating project task sync status: {str(e)}")
        self._get_connection().rollback()
        return False

def get_unsynchronized_activity_logs(self, last_id: int = 0) -> List[Dict[str, Any]]:
    """
    Get unsynchronized activity logs with improved schema handling.
    
    Args:
        last_id: ID threshold to filter by
        
    Returns:
        list: List of unsynchronized activity logs
    """
    try:
        cursor = self._get_connection().cursor()
        
        # Query for activity_logs table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activity_logs'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            logger.warning("activity_logs table does not exist in local database")
            return []
        
        # Check if 'synced' column exists
        try:
            cursor.execute("PRAGMA table_info(activity_logs)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'synced' not in column_names:
                logger.warning("'synced' column does not exist in activity_logs table")
                # Add synced column if it doesn't exist
                try:
                    cursor.execute("ALTER TABLE activity_logs ADD COLUMN synced INTEGER DEFAULT 0")
                    self._get_connection().commit()
                    logger.info("Added 'synced' column to activity_logs table")
                except Exception as add_error:
                    logger.error(f"Error adding 'synced' column: {str(add_error)}")
                    return []
        except Exception as col_error:
            logger.error(f"Error checking columns: {str(col_error)}")
            return []
            
        # Get column names from the actual table
        cursor.execute("PRAGMA table_info(activity_logs)")
        columns = cursor.fetchall()
        actual_columns = [col[1] for col in columns]
        
        # Build a dynamic query based on available columns
        query_columns = ', '.join(actual_columns)
        
        # Build query
        query = f'''
        SELECT {query_columns}
        FROM activity_logs 
        WHERE synced = 0 AND id > ?
        ORDER BY id ASC
        LIMIT 100
        '''
        
        # Execute query
        cursor.execute(query, (last_id,))
        
        # Get results
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        return [dict(zip(actual_columns, row)) for row in results]
    except Exception as e:
        logger.error(f"Error getting unsynchronized activity logs: {str(e)}")
        return []

def update_activity_log_sync_status(self, entry_id: int, synced: bool) -> bool:
    """
    Update the sync status of an activity log.
    
    Args:
        entry_id: ID of the activity log
        synced: Sync status to set
        
    Returns:
        bool: True if successful
    """
    try:
        cursor = self._get_connection().cursor()
        
        # First check which primary key column exists in the table
        cursor.execute("PRAGMA table_info(activity_logs)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Verify the id column exists
        if "id" not in column_names:
            raise ValueError("Required 'id' column not found in activity_logs table")
        
        # Update the activity log's sync status
        cursor.execute(
            'UPDATE activity_logs SET synced = ? WHERE id = ?',
            (1 if synced else 0, entry_id)
        )
        
        # Commit changes
        self._get_connection().commit()
        
        return True
    except Exception as e:
        logger.error(f"Error updating activity log sync status: {str(e)}")
        self._get_connection().rollback()
        return False

def get_unsynchronized_time_entries(self, last_id: str = '') -> List[Dict[str, Any]]:
    """
    Get unsynchronized time entries from the time_entries table.
    
    Args:
        last_id: ID threshold to filter by (UUID string)
        
    Returns:
        list: List of unsynchronized time entries
    """
    try:
        cursor = self._get_connection().cursor()
        
        # Query for time_entries table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='time_entries'")
        table_exists = cursor.fetchone() is not None
        
        if not table_exists:
            logger.warning("time_entries table does not exist in local database")
            return []
        
        # Check if 'synced' column exists
        try:
            cursor.execute("PRAGMA table_info(time_entries)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'synced' not in column_names:
                logger.warning("'synced' column does not exist in time_entries table")
                # Add synced column if it doesn't exist
                try:
                    cursor.execute("ALTER TABLE time_entries ADD COLUMN synced INTEGER DEFAULT 0")
                    self._get_connection().commit()
                    logger.info("Added 'synced' column to time_entries table")
                except Exception as add_error:
                    logger.error(f"Error adding 'synced' column: {str(add_error)}")
                    return []
        except Exception as col_error:
            logger.error(f"Error checking columns: {str(col_error)}")
            return []
            
        # Get column names from the actual table
        cursor.execute("PRAGMA table_info(time_entries)")
        columns = cursor.fetchall()
        actual_columns = [col[1] for col in columns]
        
        # Build a dynamic query based on available columns
        query_columns = ', '.join(actual_columns)
        
        # Build query - note we use string comparison for UUID
        query = f'''
        SELECT {query_columns}
        FROM time_entries 
        WHERE synced = 0 AND id > ?
        ORDER BY id ASC
        LIMIT 100
        '''
        
        # Execute query
        cursor.execute(query, (last_id,))
        
        # Get results
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        return [dict(zip(actual_columns, row)) for row in results]
    except Exception as e:
        logger.error(f"Error getting unsynchronized time entries: {str(e)}")
        return []

def update_time_entry_sync_status(self, entry_id: str, synced: bool) -> bool:
    """
    Update the sync status of a time entry in the time_entries table.
    
    Args:
        entry_id: ID of the time entry (UUID string)
        synced: Sync status to set
        
    Returns:
        bool: True if successful
    """
    try:
        cursor = self._get_connection().cursor()
        
        # First check which primary key column exists in the table
        cursor.execute("PRAGMA table_info(time_entries)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # Verify the id column exists
        if "id" not in column_names:
            raise ValueError("Required 'id' column not found in time_entries table")
        
        # Update the time entry's sync status
        cursor.execute(
            'UPDATE time_entries SET synced = ? WHERE id = ?',
            (1 if synced else 0, entry_id)
        )
        
        # Commit changes
        self._get_connection().commit()
        
        return True
    except Exception as e:
        logger.error(f"Error updating time entry sync status: {str(e)}")
        self._get_connection().rollback()
        return False
