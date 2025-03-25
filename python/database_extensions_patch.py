"""
Patches for the database service with additional methods for project task synchronization.
"""
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

def get_unsynchronized_project_tasks(self, last_id: str = "") -> List[Dict[str, Any]]:
    """
    Get unsynchronized project tasks.
    
    Args:
        last_id: ID threshold to filter by (optional)
        
    Returns:
        list: List of unsynchronized project tasks
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
            id, name, description, project_id, estimated_hours,
            is_active, synced, created_at, updated_at
        FROM project_tasks 
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
            'id', 'name', 'description', 'project_id', 'estimated_hours',
            'is_active', 'synced', 'created_at', 'updated_at'
        ]
        
        return [dict(zip(column_names, row)) for row in results]
    except Exception as e:
        logger.error(f"Error getting unsynchronized project tasks: {str(e)}")
        return []
        
def update_project_task_sync_status(self, task_id: str, synced: bool) -> bool:
    """
    Update the sync status of a project task.
    
    Args:
        task_id: ID of the project task
        synced: Sync status to set
        
    Returns:
        bool: True if successful
    """
    conn = self._get_connection()
    try:
        cursor = conn.cursor()
        
        # Update the project task sync status
        cursor.execute(
            'UPDATE project_tasks SET synced = ? WHERE id = ?',
            (1 if synced else 0, task_id)
        )
        
        # Commit changes
        conn.commit()
        
        return True
    except Exception as e:
        logger.error(f"Error updating project task sync status: {str(e)}")
        conn.rollback()
        return False
