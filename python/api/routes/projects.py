"""
Project API routes for the Time Tracker desktop app.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import uuid

from api.dependencies import get_current_user
from services.database import DatabaseService

# Setup logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)

# Create database service
db_service = DatabaseService()

# Initialize database tables if needed
def initialize_db():
    try:
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Create projects table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            client_id TEXT,
            description TEXT,
            color TEXT DEFAULT '#4CAF50',
            hourly_rate REAL DEFAULT 0,
            is_billable BOOLEAN NOT NULL DEFAULT 1,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            user_id TEXT NOT NULL,
            synced BOOLEAN NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')
        
        # Create project_tasks table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS project_tasks (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            project_id TEXT NOT NULL,
            estimated_hours REAL,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            synced BOOLEAN NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
        )
        ''')
        
        conn.commit()
        logger.info("Projects database initialized")
    except Exception as e:
        logger.error(f"Error initializing projects database: {str(e)}")

# Initialize database on startup
initialize_db()

@router.get("/")
async def list_projects(
    limit: int = 50,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List projects with pagination.
    
    Args:
        limit: Maximum number of projects to return
        offset: Number of projects to skip
        
    Returns:
        List of projects
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Build query
        query = '''
        SELECT 
            id, name, client_id, description, color, hourly_rate,
            is_billable, is_active, created_at, updated_at
        FROM projects 
        WHERE user_id = ?
        '''
        
        params = [user_id]
        
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query})"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
            
        # Add sorting and pagination
        query += ' ORDER BY name ASC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        # Execute query
        cursor.execute(query, params)
        
        # Get results
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        column_names = [
            'id', 'name', 'client_id', 'description', 'color', 'hourly_rate',
            'is_billable', 'is_active', 'created_at', 'updated_at'
        ]
        
        projects_list = [
            {
                column_names[i]: row[i] if row[i] is not None else None 
                for i in range(len(column_names))
            }
            for row in results
        ]

        # Convert boolean values
        for p in projects_list:
            p['is_billable'] = bool(p['is_billable'])
            p['is_active'] = bool(p['is_active'])
        
        return {
            "total": total,
            "projects": projects_list
        }
    except Exception as e:
        logger.error(f"Error getting projects: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get projects: {str(e)}")

@router.get("/{project_id}")
async def get_project(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a project by ID.
    
    Args:
        project_id: The ID of the project to retrieve
        
    Returns:
        The project
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Get the project
        cursor.execute(
            '''
            SELECT 
                id, name, client_id, description, color, hourly_rate,
                is_billable, is_active, created_at, updated_at
            FROM projects 
            WHERE id = ? AND user_id = ?
            ''',
            (project_id, user_id)
        )
        
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")
            
        # Convert to dictionary
        column_names = [
            'id', 'name', 'client_id', 'description', 'color', 'hourly_rate',
            'is_billable', 'is_active', 'created_at', 'updated_at'
        ]
        
        project = {
            column_names[i]: row[i] if row[i] is not None else None 
            for i in range(len(column_names))
        }
        
        # Convert boolean values
        project['is_billable'] = bool(project['is_billable'])
        project['is_active'] = bool(project['is_active'])
        
        return {"project": project}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get project: {str(e)}")

@router.post("/")
async def create_project(
    project: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new project.
    
    Args:
        project: The project data
        
    Returns:
        The created project
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
            
        # Validate required fields
        if not project.get("name"):
            raise HTTPException(status_code=400, detail="Project name is required")
            
        # Generate a UUID for the project
        project_id = str(uuid.uuid4())
        
        # Get current timestamp
        now = datetime.now().isoformat()
        
        # Default values
        color = project.get("color", "#4CAF50")  # Default to green
        hourly_rate = project.get("hourly_rate", 0)
        is_billable = 1 if project.get("is_billable", True) else 0
        
        # Prepare query and parameters
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            '''
            INSERT INTO projects 
            (id, name, client_id, description, color, hourly_rate, 
            is_billable, is_active, user_id, synced, created_at, updated_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                project_id,
                project.get("name"),
                project.get("client_id"),
                project.get("description"),
                color,
                hourly_rate,
                is_billable,
                1,  # is_active = True
                user_id,
                0,  # Not synced
                now,
                now
            )
        )
        
        conn.commit()
        
        # Create response project object
        new_project = {
            "id": project_id,
            "name": project.get("name"),
            "client_id": project.get("client_id"),
            "description": project.get("description"),
            "color": color,
            "hourly_rate": hourly_rate,
            "is_billable": bool(is_billable),
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        
        logger.info(f"Created project {project_id}")
        
        return {"project": new_project}
    
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

@router.put("/{project_id}")
async def update_project(
    project_id: str,
    project_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update a project.
    
    Args:
        project_id: The ID of the project to update
        project_data: The project data to update
        
    Returns:
        The updated project
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # First check if the project exists and belongs to the user
        cursor.execute(
            'SELECT COUNT(*) FROM projects WHERE id = ? AND user_id = ?',
            (project_id, user_id)
        )
        
        count = cursor.fetchone()[0]
        if count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Build SET clause for SQL query
        set_clauses = []
        params = []
        
        updateable_fields = [
            'name', 'client_id', 'description', 'color', 
            'hourly_rate', 'is_billable', 'is_active'
        ]
        
        for field in updateable_fields:
            if field in project_data:
                set_clauses.append(f"{field} = ?")
                
                # Convert boolean values for SQLite
                if field in ['is_billable', 'is_active']:
                    params.append(1 if project_data[field] else 0)
                else:
                    params.append(project_data[field])
        
        # Add updated_at timestamp
        set_clauses.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        
        # Add project_id and user_id to parameters
        params.extend([project_id, user_id])
        
        # Execute update if there are fields to update
        if set_clauses:
            cursor.execute(
                f'''
                UPDATE projects 
                SET {", ".join(set_clauses)}
                WHERE id = ? AND user_id = ?
                ''',
                tuple(params)
            )
            
            conn.commit()
        
        # Get and return the updated project
        return await get_project(project_id, current_user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update project: {str(e)}")

@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a project.
    
    Args:
        project_id: The ID of the project to delete
        
    Returns:
        Success message
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # First get the project to return it in the response
        cursor.execute(
            '''
            SELECT 
                id, name, client_id, description, color, hourly_rate,
                is_billable, is_active, created_at, updated_at
            FROM projects 
            WHERE id = ? AND user_id = ?
            ''',
            (project_id, user_id)
        )
        
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")
            
        # Convert to dictionary
        column_names = [
            'id', 'name', 'client_id', 'description', 'color', 'hourly_rate',
            'is_billable', 'is_active', 'created_at', 'updated_at'
        ]
        
        deleted_project = {
            column_names[i]: row[i] if row[i] is not None else None 
            for i in range(len(column_names))
        }
        
        # Convert boolean values
        deleted_project['is_billable'] = bool(deleted_project['is_billable'])
        deleted_project['is_active'] = bool(deleted_project['is_active'])
        
        # Delete project (and tasks via ON DELETE CASCADE)
        cursor.execute(
            'DELETE FROM projects WHERE id = ? AND user_id = ?',
            (project_id, user_id)
        )
        
        conn.commit()
        
        logger.info(f"Deleted project {project_id}")
        
        return {"project": deleted_project}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")

# Project tasks endpoints

@router.get("/{project_id}/tasks")
async def list_project_tasks(
    project_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List tasks for a project with pagination.
    
    Args:
        project_id: The ID of the project
        limit: Maximum number of tasks to return
        offset: Number of tasks to skip
        
    Returns:
        List of tasks
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # First check if the project exists and belongs to the user
        cursor.execute(
            'SELECT COUNT(*) FROM projects WHERE id = ? AND user_id = ?',
            (project_id, user_id)
        )
        
        count = cursor.fetchone()[0]
        if count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Build query to get tasks for this project
        query = '''
        SELECT 
            id, name, description, project_id, estimated_hours,
            is_active, created_at, updated_at
        FROM project_tasks 
        WHERE project_id = ?
        '''
        
        params = [project_id]
        
        # Count total
        count_query = f"SELECT COUNT(*) FROM ({query})"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]
            
        # Add sorting and pagination
        query += ' ORDER BY name ASC LIMIT ? OFFSET ?'
        params.extend([limit, offset])
        
        # Execute query
        cursor.execute(query, params)
        
        # Get results
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        column_names = [
            'id', 'name', 'description', 'project_id', 'estimated_hours',
            'is_active', 'created_at', 'updated_at'
        ]
        
        tasks_list = [
            {
                column_names[i]: row[i] if row[i] is not None else None 
                for i in range(len(column_names))
            }
            for row in results
        ]

        # Convert boolean values
        for t in tasks_list:
            t['is_active'] = bool(t['is_active'])
        
        return {
            "total": total,
            "tasks": tasks_list
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting project tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get project tasks: {str(e)}")

@router.post("/{project_id}/tasks")
async def create_project_task(
    project_id: str,
    task: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new task for a project.
    
    Args:
        project_id: The ID of the project
        task: The task data
        
    Returns:
        The created task
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
            
        # Validate required fields
        if not task.get("name"):
            raise HTTPException(status_code=400, detail="Task name is required")
            
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Check if the project exists and belongs to the user
        cursor.execute(
            'SELECT COUNT(*) FROM projects WHERE id = ? AND user_id = ?',
            (project_id, user_id)
        )
        
        count = cursor.fetchone()[0]
        if count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Generate a UUID for the task
        task_id = str(uuid.uuid4())
        
        # Get current timestamp
        now = datetime.now().isoformat()
        
        # Prepare query and parameters
        cursor.execute(
            '''
            INSERT INTO project_tasks 
            (id, name, description, project_id, estimated_hours, 
            is_active, synced, created_at, updated_at) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''',
            (
                task_id,
                task.get("name"),
                task.get("description"),
                project_id,
                task.get("estimated_hours"),
                1,  # is_active = True
                0,  # Not synced
                now,
                now
            )
        )
        
        conn.commit()
        
        # Create response task object
        new_task = {
            "id": task_id,
            "name": task.get("name"),
            "description": task.get("description"),
            "project_id": project_id,
            "estimated_hours": task.get("estimated_hours"),
            "is_active": True,
            "created_at": now,
            "updated_at": now
        }
        
        logger.info(f"Created task {task_id} for project {project_id}")
        
        return {"task": new_task}
    
    except Exception as e:
        logger.error(f"Error creating project task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create project task: {str(e)}")

@router.put("/{project_id}/tasks/{task_id}")
async def update_project_task(
    project_id: str,
    task_id: str,
    task_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update a task for a project.
    
    Args:
        project_id: The ID of the project
        task_id: The ID of the task to update
        task_data: The task data to update
        
    Returns:
        The updated task
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # First check if the project exists and belongs to the user
        cursor.execute(
            'SELECT COUNT(*) FROM projects WHERE id = ? AND user_id = ?',
            (project_id, user_id)
        )
        
        count = cursor.fetchone()[0]
        if count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Then check if the task exists for this project
        cursor.execute(
            'SELECT COUNT(*) FROM project_tasks WHERE id = ? AND project_id = ?',
            (task_id, project_id)
        )
        
        count = cursor.fetchone()[0]
        if count == 0:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Build SET clause for SQL query
        set_clauses = []
        params = []
        
        updateable_fields = [
            'name', 'description', 'estimated_hours', 'is_active'
        ]
        
        for field in updateable_fields:
            if field in task_data:
                set_clauses.append(f"{field} = ?")
                
                # Convert boolean values for SQLite
                if field == 'is_active':
                    params.append(1 if task_data[field] else 0)
                else:
                    params.append(task_data[field])
        
        # Add updated_at timestamp
        set_clauses.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        
        # Add task_id and project_id to parameters
        params.extend([task_id, project_id])
        
        # Execute update if there are fields to update
        if set_clauses:
            cursor.execute(
                f'''
                UPDATE project_tasks 
                SET {", ".join(set_clauses)}
                WHERE id = ? AND project_id = ?
                ''',
                tuple(params)
            )
            
            conn.commit()
        
        # Get the updated task
        cursor.execute(
            '''
            SELECT 
                id, name, description, project_id, estimated_hours,
                is_active, created_at, updated_at
            FROM project_tasks 
            WHERE id = ? AND project_id = ?
            ''',
            (task_id, project_id)
        )
        
        row = cursor.fetchone()
        
        # Convert to dictionary
        column_names = [
            'id', 'name', 'description', 'project_id', 'estimated_hours',
            'is_active', 'created_at', 'updated_at'
        ]
        
        updated_task = {
            column_names[i]: row[i] if row[i] is not None else None 
            for i in range(len(column_names))
        }
        
        # Convert boolean values
        updated_task['is_active'] = bool(updated_task['is_active'])
        
        logger.info(f"Updated task {task_id} for project {project_id}")
        
        return {"task": updated_task}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update task: {str(e)}")

@router.delete("/{project_id}/tasks/{task_id}")
async def delete_project_task(
    project_id: str,
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a task for a project.
    
    Args:
        project_id: The ID of the project
        task_id: The ID of the task to delete
        
    Returns:
        Success message
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # First check if the project exists and belongs to the user
        cursor.execute(
            'SELECT COUNT(*) FROM projects WHERE id = ? AND user_id = ?',
            (project_id, user_id)
        )
        
        count = cursor.fetchone()[0]
        if count == 0:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Then get the task to return it in the response
        cursor.execute(
            '''
            SELECT 
                id, name, description, project_id, estimated_hours,
                is_active, created_at, updated_at
            FROM project_tasks 
            WHERE id = ? AND project_id = ?
            ''',
            (task_id, project_id)
        )
        
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Task not found")
            
        # Convert to dictionary
        column_names = [
            'id', 'name', 'description', 'project_id', 'estimated_hours',
            'is_active', 'created_at', 'updated_at'
        ]
        
        deleted_task = {
            column_names[i]: row[i] if row[i] is not None else None 
            for i in range(len(column_names))
        }
        
        # Convert boolean values
        deleted_task['is_active'] = bool(deleted_task['is_active'])
        
        # Delete the task
        cursor.execute(
            'DELETE FROM project_tasks WHERE id = ? AND project_id = ?',
            (task_id, project_id)
        )
        
        conn.commit()
        
        logger.info(f"Deleted task {task_id} for project {project_id}")
        
        return {"task": deleted_task}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")
