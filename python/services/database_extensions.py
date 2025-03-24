"""
Extension methods for the DatabaseService class to handle clients, projects, and settings.
"""
import os
import sqlite3
import logging
import uuid
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

# Setup logger
logger = logging.getLogger(__name__)

# Client methods
def create_client(self, name: str, user_id: str, **kwargs) -> Dict[str, Any]:
    """
    Create a new client.
    
    Args:
        name: Name of the client
        user_id: ID of the user who created the client
        **kwargs: Additional client data
        
    Returns:
        dict: The created client
    """
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Generate a UUID for the client
        client_id = str(uuid.uuid4())
        
        # Get current timestamp for created_at and updated_at
        current_time = datetime.now().isoformat()
        
        # Prepare query and parameters
        fields = ['id', 'name', 'user_id', 'created_at', 'updated_at']
        values = [client_id, name, user_id, current_time, current_time]
        
        # Add optional fields
        optional_fields = [
            'contact_name', 'email', 'phone', 'address', 'notes'
        ]
        
        for field in optional_fields:
            if field in kwargs and kwargs[field] is not None:
                fields.append(field)
                values.append(kwargs[field])
        
        # Set is_active to true by default
        if 'is_active' not in fields:
            fields.append('is_active')
            values.append(1)  # 1 = True in SQLite
            
        # Create placeholders for SQL query
        placeholders = ', '.join('?' for _ in range(len(fields)))
        fields_str = ', '.join(fields)
        
        # Create new client
        cursor.execute(
            f'''
            INSERT INTO clients 
            ({fields_str}) 
            VALUES ({placeholders})
            ''',
            values
        )
        
        # Commit changes
        conn.commit()
        
        # Return the created client
        return self.get_client(client_id)
    except Exception as e:
        logger.error(f"Error creating client: {str(e)}")
        conn.rollback()
        raise

def get_client(self, client_id: str) -> Dict[str, Any]:
    """
    Get a client by ID.
    
    Args:
        client_id: ID of the client to get
        
    Returns:
        dict: The client
    """
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get the client
        cursor.execute(
            '''
            SELECT 
                id, name, contact_name, email, phone, address, notes,
                is_active, user_id, created_at, updated_at, synced
            FROM clients 
            WHERE id = ?
            ''',
            (client_id,)
        )
        
        client = cursor.fetchone()
        
        if not client:
            logger.warning(f"Client not found: {client_id}")
            return {}
            
        # Convert to dictionary
        column_names = [
            'id', 'name', 'contact_name', 'email', 'phone', 'address', 'notes',
            'is_active', 'user_id', 'created_at', 'updated_at', 'synced'
        ]
        
        return dict(zip(column_names, client))
    except Exception as e:
        logger.error(f"Error getting client: {str(e)}")
        return {}

def update_client(self, client_id: str, **kwargs) -> Dict[str, Any]:
    """
    Update a client.
    
    Args:
        client_id: ID of the client to update
        **kwargs: Fields to update
        
    Returns:
        dict: The updated client
    """
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Build SET clause for SQL query
        set_clause = []
        params = []
        
        updateable_fields = [
            'name', 'contact_name', 'email', 'phone', 
            'address', 'notes', 'is_active'
        ]
        
        for field in updateable_fields:
            if field in kwargs and kwargs[field] is not None:
                set_clause.append(f"{field} = ?")
                params.append(kwargs[field])
        
        # Add updated_at timestamp
        set_clause.append("updated_at = CURRENT_TIMESTAMP")
        
        # Add client_id to params
        params.append(client_id)
        
        if not set_clause:
            logger.warning(f"No fields to update for client: {client_id}")
            return self.get_client(client_id)
        
        # Update client
        cursor.execute(
            f'''
            UPDATE clients 
            SET {', '.join(set_clause)}
            WHERE id = ?
            ''',
            params
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
        bool: True if client was deleted
    """
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Delete client
        cursor.execute(
            'DELETE FROM clients WHERE id = ?',
            (client_id,)
        )
        
        # Commit changes
        conn.commit()
        
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error deleting client: {str(e)}")
        conn.rollback()
        return False

def get_clients(
    self,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    synced: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """
    Get clients with optional filtering.
    
    Args:
        limit: Maximum number of clients to return
        offset: Offset for pagination
        user_id: Filter by user ID
        is_active: Filter by active status
        synced: Filter by synced status
        
    Returns:
        list: List of clients
    """
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Build query
        query = '''
        SELECT 
            id, name, contact_name, email, phone, address, notes,
            is_active, user_id, created_at, updated_at, synced
        FROM clients 
        WHERE 1=1
        '''
        
        params = []
        
        # Add filters
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
            
        if is_active is not None:
            query += ' AND is_active = ?'
            params.append(1 if is_active else 0)
            
        if synced is not None:
            query += ' AND synced = ?'
            params.append(1 if synced else 0)
            
        # Add sorting and pagination
        query += ' ORDER BY name LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        # Execute query
        cursor.execute(query, params)
        
        # Get results
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        column_names = [
            'id', 'name', 'contact_name', 'email', 'phone', 'address', 'notes',
            'is_active', 'user_id', 'created_at', 'updated_at', 'synced'
        ]
        
        return [dict(zip(column_names, row)) for row in results]
    except Exception as e:
        logger.error(f"Error getting clients: {str(e)}")
        return []

# Project methods
def create_project(self, name: str, user_id: str, **kwargs) -> Dict[str, Any]:
    """
    Create a new project.
    
    Args:
        name: Name of the project
        user_id: ID of the user who created the project
        **kwargs: Additional project data
        
    Returns:
        dict: The created project
    """
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Generate a UUID for the project
        project_id = str(uuid.uuid4())
        
        # Get current timestamp for created_at and updated_at
        current_time = datetime.now().isoformat()
        
        # Prepare query and parameters
        fields = ['id', 'name', 'user_id', 'created_at', 'updated_at']
        values = [project_id, name, user_id, current_time, current_time]
        
        # Add optional fields
        optional_fields = [
            'client_id', 'description', 'color', 'hourly_rate', 'is_billable'
        ]
        
        for field in optional_fields:
            if field in kwargs and kwargs[field] is not None:
                fields.append(field)
                values.append(kwargs[field])
        
        # Set is_active and is_billable to true by default
        if 'is_active' not in fields:
            fields.append('is_active')
            values.append(1)  # 1 = True in SQLite
            
        if 'is_billable' not in fields:
            fields.append('is_billable')
            values.append(1)  # 1 = True in SQLite
            
        # Create placeholders for SQL query
        placeholders = ', '.join('?' for _ in range(len(fields)))
        fields_str = ', '.join(fields)
        
        # Create new project
        cursor.execute(
            f'''
            INSERT INTO projects 
            ({fields_str}) 
            VALUES ({placeholders})
            ''',
            values
        )
        
        # Commit changes
        conn.commit()
        
        # Return the created project
        return self.get_project(project_id)
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        conn.rollback()
        raise

def get_project(self, project_id: str) -> Dict[str, Any]:
    """
    Get a project by ID.
    
    Args:
        project_id: ID of the project to get
        
    Returns:
        dict: The project
    """
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get the project
        cursor.execute(
            '''
            SELECT 
                id, name, description, client_id, color, hourly_rate,
                is_billable, is_active, user_id, created_at, updated_at, synced
            FROM projects 
            WHERE id = ?
            ''',
            (project_id,)
        )
        
        project = cursor.fetchone()
        
        if not project:
            logger.warning(f"Project not found: {project_id}")
            return {}
            
        # Convert to dictionary
        column_names = [
            'id', 'name', 'description', 'client_id', 'color', 'hourly_rate',
            'is_billable', 'is_active', 'user_id', 'created_at', 'updated_at', 'synced'
        ]
        
        return dict(zip(column_names, project))
    except Exception as e:
        logger.error(f"Error getting project: {str(e)}")
        return {}

def update_project(self, project_id: str, **kwargs) -> Dict[str, Any]:
    """
    Update a project.
    
    Args:
        project_id: ID of the project to update
        **kwargs: Fields to update
        
    Returns:
        dict: The updated project
    """
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Build SET clause for SQL query
        set_clause = []
        params = []
        
        updateable_fields = [
            'name', 'description', 'client_id', 'color', 
            'hourly_rate', 'is_billable', 'is_active'
        ]
        
        for field in updateable_fields:
            if field in kwargs and kwargs[field] is not None:
                set_clause.append(f"{field} = ?")
                params.append(kwargs[field])
        
        # Add updated_at timestamp
        set_clause.append("updated_at = CURRENT_TIMESTAMP")
        
        # Add project_id to params
        params.append(project_id)
        
        if not set_clause:
            logger.warning(f"No fields to update for project: {project_id}")
            return self.get_project(project_id)
        
        # Update project
        cursor.execute(
            f'''
            UPDATE projects 
            SET {', '.join(set_clause)}
            WHERE id = ?
            ''',
            params
        )
        
        # Commit changes
        conn.commit()
        
        # Return the updated project
        return self.get_project(project_id)
    except Exception as e:
        logger.error(f"Error updating project: {str(e)}")
        conn.rollback()
        return {}

def delete_project(self, project_id: str) -> bool:
    """
    Delete a project.
    
    Args:
        project_id: ID of the project to delete
        
    Returns:
        bool: True if project was deleted
    """
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Delete project
        cursor.execute(
            'DELETE FROM projects WHERE id = ?',
            (project_id,)
        )
        
        # Commit changes
        conn.commit()
        
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        conn.rollback()
        return False

def get_projects(
    self,
    limit: int = 50,
    offset: int = 0,
    user_id: Optional[str] = None,
    client_id: Optional[str] = None,
    is_active: Optional[bool] = None,
    synced: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """
    Get projects with optional filtering.
    
    Args:
        limit: Maximum number of projects to return
        offset: Offset for pagination
        user_id: Filter by user ID
        client_id: Filter by client ID
        is_active: Filter by active status
        synced: Filter by synced status
        
    Returns:
        list: List of projects
    """
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Build query
        query = '''
        SELECT 
            id, name, description, client_id, color, hourly_rate,
            is_billable, is_active, user_id, created_at, updated_at, synced
        FROM projects 
        WHERE 1=1
        '''
        
        params = []
        
        # Add filters
        if user_id:
            query += ' AND user_id = ?'
            params.append(user_id)
            
        if client_id:
            query += ' AND client_id = ?'
            params.append(client_id)
            
        if is_active is not None:
            query += ' AND is_active = ?'
            params.append(1 if is_active else 0)
            
        if synced is not None:
            query += ' AND synced = ?'
            params.append(1 if synced else 0)
            
        # Add sorting and pagination
        query += ' ORDER BY name LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        # Execute query
        cursor.execute(query, params)
        
        # Get results
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        column_names = [
            'id', 'name', 'description', 'client_id', 'color', 'hourly_rate',
            'is_billable', 'is_active', 'user_id', 'created_at', 'updated_at', 'synced'
        ]
        
        return [dict(zip(column_names, row)) for row in results]
    except Exception as e:
        logger.error(f"Error getting projects: {str(e)}")
        return []

# Project Task methods
def create_project_task(self, name: str, project_id: str, **kwargs) -> Dict[str, Any]:
    """
    Create a new project task.
    
    Args:
        name: Name of the task
        project_id: ID of the project
        **kwargs: Additional task data
        
    Returns:
        dict: The created task
    """
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Generate a UUID for the task
        task_id = str(uuid.uuid4())
        
        # Get current timestamp for created_at and updated_at
        current_time = datetime.now().isoformat()
        
        # Prepare query and parameters
        fields = ['id', 'name', 'project_id', 'created_at', 'updated_at']
        values = [task_id, name, project_id, current_time, current_time]
        
        # Add optional fields
        optional_fields = ['description', 'estimated_hours']
        
        for field in optional_fields:
            if field in kwargs and kwargs[field] is not None:
                fields.append(field)
                values.append(kwargs[field])
        
        # Set is_active to true by default
        if 'is_active' not in fields:
            fields.append('is_active')
            values.append(1)  # 1 = True in SQLite
            
        # Create placeholders for SQL query
        placeholders = ', '.join('?' for _ in range(len(fields)))
        fields_str = ', '.join(fields)
        
        # Create new task
        cursor.execute(
            f'''
            INSERT INTO project_tasks 
            ({fields_str}) 
            VALUES ({placeholders})
            ''',
            values
        )
        
        # Commit changes
        conn.commit()
        
        # Return the created task
        return self.get_project_task(task_id)
    except Exception as e:
        logger.error(f"Error creating project task: {str(e)}")
        conn.rollback()
        raise

def get_project_task(self, task_id: str) -> Dict[str, Any]:
    """
    Get a project task by ID.
    
    Args:
        task_id: ID of the task to get
        
    Returns:
        dict: The task
    """
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get the task
        cursor.execute(
            '''
            SELECT 
                id, name, description, project_id, estimated_hours,
                is_active, created_at, updated_at, synced
            FROM project_tasks 
            WHERE id = ?
            ''',
            (task_id,)
        )
        
        task = cursor.fetchone()
        
        if not task:
            logger.warning(f"Project task not found: {task_id}")
            return {}
            
        # Convert to dictionary
        column_names = [
            'id', 'name', 'description', 'project_id', 'estimated_hours',
            'is_active', 'created_at', 'updated_at', 'synced'
        ]
        
        return dict(zip(column_names, task))
    except Exception as e:
        logger.error(f"Error getting project task: {str(e)}")
        return {}

def update_project_task(self, task_id: str, **kwargs) -> Dict[str, Any]:
    """
    Update a project task.
    
    Args:
        task_id: ID of the task to update
        **kwargs: Fields to update
        
    Returns:
        dict: The updated task
    """
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Build SET clause for SQL query
        set_clause = []
        params = []
        
        updateable_fields = [
            'name', 'description', 'estimated_hours', 'is_active'
        ]
        
        for field in updateable_fields:
            if field in kwargs and kwargs[field] is not None:
                set_clause.append(f"{field} = ?")
                params.append(kwargs[field])
        
        # Add updated_at timestamp
        set_clause.append("updated_at = CURRENT_TIMESTAMP")
        
        # Add task_id to params
        params.append(task_id)
        
        if not set_clause:
            logger.warning(f"No fields to update for task: {task_id}")
            return self.get_project_task(task_id)
        
        # Update task
        cursor.execute(
            f'''
            UPDATE project_tasks 
            SET {', '.join(set_clause)}
            WHERE id = ?
            ''',
            params
        )
        
        # Commit changes
        conn.commit()
        
        # Return the updated task
        return self.get_project_task(task_id)
    except Exception as e:
        logger.error(f"Error updating project task: {str(e)}")
        conn.rollback()
        return {}

def delete_project_task(self, task_id: str) -> bool:
    """
    Delete a project task.
    
    Args:
        task_id: ID of the task to delete
        
    Returns:
        bool: True if task was deleted
    """
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Delete task
        cursor.execute(
            'DELETE FROM project_tasks WHERE id = ?',
            (task_id,)
        )
        
        # Commit changes
        conn.commit()
        
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Error deleting project task: {str(e)}")
        conn.rollback()
        return False

def get_project_tasks(
    self,
    project_id: str,
    limit: int = 50,
    offset: int = 0,
    is_active: Optional[bool] = None,
    synced: Optional[bool] = None
) -> List[Dict[str, Any]]:
    """
    Get tasks for a project.
    
    Args:
        project_id: ID of the project
        limit: Maximum number of tasks to return
        offset: Offset for pagination
        is_active: Filter by active status
        synced: Filter by synced status
        
    Returns:
        list: List of tasks
    """
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Build query
        query = '''
        SELECT 
            id, name, description, project_id, estimated_hours,
            is_active, created_at, updated_at, synced
        FROM project_tasks 
        WHERE project_id = ?
        '''
        
        params = [project_id]
        
        # Add filters
        if is_active is not None:
            query += ' AND is_active = ?'
            params.append(1 if is_active else 0)
            
        if synced is not None:
            query += ' AND synced = ?'
            params.append(1 if synced else 0)
            
        # Add sorting and pagination
        query += ' ORDER BY name LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        # Execute query
        cursor.execute(query, params)
        
        # Get results
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        column_names = [
            'id', 'name', 'description', 'project_id', 'estimated_hours',
            'is_active', 'created_at', 'updated_at', 'synced'
        ]
        
        return [dict(zip(column_names, row)) for row in results]
    except Exception as e:
        logger.error(f"Error getting project tasks: {str(e)}")
        return []

# User Settings methods
def get_user_settings(self, user_id: str) -> Dict[str, Any]:
    """
    Get settings for a user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        dict: The user's settings
    """
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get the settings
        cursor.execute(
            '''
            SELECT 
                user_id, screenshot_interval, screenshot_quality, 
                auto_sync_interval, idle_detection_timeout, theme,
                notifications_enabled, created_at, updated_at, synced
            FROM user_settings 
            WHERE user_id = ?
            ''',
            (user_id,)
        )
        
        settings = cursor.fetchone()
        
        if not settings:
            # Create default settings
            cursor.execute(
                '''
                INSERT INTO user_settings 
                (user_id) 
                VALUES (?)
                ''',
                (user_id,)
            )
            
            conn.commit()
            
            # Try again
            cursor.execute(
                '''
                SELECT 
                    user_id, screenshot_interval, screenshot_quality, 
                    auto_sync_interval, idle_detection_timeout, theme,
                    notifications_enabled, created_at, updated_at, synced
                FROM user_settings 
                WHERE user_id = ?
                ''',
                (user_id,)
            )
            
            settings = cursor.fetchone()
            
        # Convert to dictionary
        column_names = [
            'user_id', 'screenshot_interval', 'screenshot_quality', 
            'auto_sync_interval', 'idle_detection_timeout', 'theme',
            'notifications_enabled', 'created_at', 'updated_at', 'synced'
        ]
        
        return dict(zip(column_names, settings))
    except Exception as e:
        logger.error(f"Error getting user settings: {str(e)}")
        return {}

def update_user_settings(self, user_id: str, **kwargs) -> Dict[str, Any]:
    """
    Update settings for a user.
    
    Args:
        user_id: ID of the user
        **kwargs: Settings to update
        
    Returns:
        dict: The updated settings
    """
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get current settings
        current_settings = self.get_user_settings(user_id)
        
        # If no settings exist, ensure user_id exists in the table
        if not current_settings:
            cursor.execute(
                '''
                INSERT OR IGNORE INTO user_settings 
                (user_id) 
                VALUES (?)
                ''',
                (user_id,)
            )
        
        # Build SET clause for SQL query
        set_clause = []
        params = []
        
        updateable_fields = [
            'screenshot_interval', 'screenshot_quality', 
            'auto_sync_interval', 'idle_detection_timeout', 
            'theme', 'notifications_enabled'
        ]
        
        for field in updateable_fields:
            if field in kwargs and kwargs[field] is not None:
                set_clause.append(f"{field} = ?")
                params.append(kwargs[field])
        
        if not set_clause:
            logger.warning(f"No settings to update for user: {user_id}")
            return self.get_user_settings(user_id)
        
        # Add updated_at timestamp
        set_clause.append("updated_at = CURRENT_TIMESTAMP")
        set_clause.append("synced = 0")
        
        # Add user_id to params
        params.append(user_id)
        
        # Update settings
        cursor.execute(
            f'''
            UPDATE user_settings 
            SET {', '.join(set_clause)}
            WHERE user_id = ?
            ''',
            params
        )
        
        # Commit changes
        conn.commit()
        
        # Return the updated settings
        return self.get_user_settings(user_id)
    except Exception as e:
        logger.error(f"Error updating user settings: {str(e)}")
        conn.rollback()
        return {}

# User Profile methods
def get_user_profile(self, user_id: str) -> Dict[str, Any]:
    """
    Get profile for a user.
    
    Args:
        user_id: ID of the user
        
    Returns:
        dict: The user's profile
    """
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get the profile
        cursor.execute(
            '''
            SELECT 
                user_id, name, email, timezone, hourly_rate,
                avatar_url, created_at, updated_at, synced
            FROM user_profiles 
            WHERE user_id = ?
            ''',
            (user_id,)
        )
        
        profile = cursor.fetchone()
        
        if not profile:
            # Create default profile
            cursor.execute(
                '''
                INSERT INTO user_profiles 
                (user_id) 
                VALUES (?)
                ''',
                (user_id,)
            )
            
            conn.commit()
            
            # Try again
            cursor.execute(
                '''
                SELECT 
                    user_id, name, email, timezone, hourly_rate,
                    avatar_url, created_at, updated_at, synced
                FROM user_profiles 
                WHERE user_id = ?
                ''',
                (user_id,)
            )
            
            profile = cursor.fetchone()
            
        # Convert to dictionary
        column_names = [
            'user_id', 'name', 'email', 'timezone', 'hourly_rate',
            'avatar_url', 'created_at', 'updated_at', 'synced'
        ]
        
        return dict(zip(column_names, profile))
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        return {}

def update_user_profile(self, user_id: str, **kwargs) -> Dict[str, Any]:
    """
    Update profile for a user.
    
    Args:
        user_id: ID of the user
        **kwargs: Profile fields to update
        
    Returns:
        dict: The updated profile
    """
    try:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get current profile
        current_profile = self.get_user_profile(user_id)
        
        # If no profile exists, ensure user_id exists in the table
        if not current_profile:
            cursor.execute(
                '''
                INSERT OR IGNORE INTO user_profiles 
                (user_id) 
                VALUES (?)
                ''',
                (user_id,)
            )
        
        # Build SET clause for SQL query
        set_clause = []
        params = []
        
        updateable_fields = [
            'name', 'email', 'timezone', 'hourly_rate', 'avatar_url'
        ]
        
        for field in updateable_fields:
            if field in kwargs and kwargs[field] is not None:
                set_clause.append(f"{field} = ?")
                params.append(kwargs[field])
        
        if not set_clause:
            logger.warning(f"No profile fields to update for user: {user_id}")
            return self.get_user_profile(user_id)
        
        # Add updated_at timestamp
        set_clause.append("updated_at = CURRENT_TIMESTAMP")
        set_clause.append("synced = 0")
        
        # Add user_id to params
        params.append(user_id)
        
        # Update profile
        cursor.execute(
            f'''
            UPDATE user_profiles 
            SET {', '.join(set_clause)}
            WHERE user_id = ?
            ''',
            params
        )
        
        # Commit changes
        conn.commit()
        
        # Return the updated profile
        return self.get_user_profile(user_id)
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        conn.rollback()
        return {}
