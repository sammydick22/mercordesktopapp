"""
Project API routes for the Time Tracker desktop app.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import uuid

from api.dependencies import get_current_user

# Setup logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/projects",
    tags=["projects"],
    responses={404: {"description": "Not found"}},
)

# Temporary placeholder for project data
# In the real implementation, this will use Supabase
projects = []
tasks = []

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
    start = offset
    end = offset + limit
    
    return {
        "total": len(projects),
        "projects": projects[start:end]
    }

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
    for project in projects:
        if project["id"] == project_id:
            return {"project": project}
    
    raise HTTPException(status_code=404, detail="Project not found")

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
    now = datetime.utcnow().isoformat()
    
    # Create new project
    new_project = {
        "id": str(uuid.uuid4()),
        "name": project.get("name"),
        "client_id": project.get("client_id"),
        "description": project.get("description"),
        "color": project.get("color", "#4CAF50"),  # Default to green
        "hourly_rate": project.get("hourly_rate"),
        "is_billable": project.get("is_billable", True),
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }
    
    # Store the project
    projects.append(new_project)
    
    logger.info(f"Created project {new_project['id']}")
    
    return {"project": new_project}

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
    for project in projects:
        if project["id"] == project_id:
            # Update project fields
            for key, value in project_data.items():
                if key in project:
                    project[key] = value
            
            # Update the updated_at timestamp
            project["updated_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Updated project {project_id}")
            
            return {"project": project}
    
    raise HTTPException(status_code=404, detail="Project not found")

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
    for i, project in enumerate(projects):
        if project["id"] == project_id:
            # Remove the project
            deleted_project = projects.pop(i)
            
            # Also remove associated tasks
            global tasks
            tasks = [task for task in tasks if task["project_id"] != project_id]
            
            logger.info(f"Deleted project {project_id}")
            
            return {"project": deleted_project}
    
    raise HTTPException(status_code=404, detail="Project not found")

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
    # Check if project exists
    project_exists = any(p["id"] == project_id for p in projects)
    if not project_exists:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Filter tasks for this project
    project_tasks = [task for task in tasks if task["project_id"] == project_id]
    
    start = offset
    end = offset + limit
    
    return {
        "total": len(project_tasks),
        "tasks": project_tasks[start:end]
    }

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
    # Check if project exists
    project_exists = any(p["id"] == project_id for p in projects)
    if not project_exists:
        raise HTTPException(status_code=404, detail="Project not found")
    
    now = datetime.utcnow().isoformat()
    
    # Create new task
    new_task = {
        "id": str(uuid.uuid4()),
        "name": task.get("name"),
        "description": task.get("description"),
        "project_id": project_id,
        "estimated_hours": task.get("estimated_hours"),
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }
    
    # Store the task
    tasks.append(new_task)
    
    logger.info(f"Created task {new_task['id']} for project {project_id}")
    
    return {"task": new_task}

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
    # Find the task
    for task in tasks:
        if task["id"] == task_id and task["project_id"] == project_id:
            # Update task fields
            for key, value in task_data.items():
                if key in task:
                    task[key] = value
            
            # Update the updated_at timestamp
            task["updated_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Updated task {task_id} for project {project_id}")
            
            return {"task": task}
    
    raise HTTPException(status_code=404, detail="Task not found")

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
    for i, task in enumerate(tasks):
        if task["id"] == task_id and task["project_id"] == project_id:
            # Remove the task
            deleted_task = tasks.pop(i)
            
            logger.info(f"Deleted task {task_id} for project {project_id}")
            
            return {"task": deleted_task}
    
    raise HTTPException(status_code=404, detail="Task not found")
