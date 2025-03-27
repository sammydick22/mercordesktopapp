"""
Insightful-style API routes that interface with the local database.
These endpoints implement the Insightful API structure but use the local database.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, Dict, Any
import logging
from datetime import datetime

from api.dependencies import get_current_user, get_db_service

# Setup logger
logger = logging.getLogger(__name__)

# Create router with prefix
router = APIRouter(
    prefix="/insightful",
    tags=["insightful"],
    responses={404: {"description": "Not found"}},
)

# Get database service
from api.dependencies import get_db_service

@router.delete("/project/{project_id}")
async def delete_insightful_project(
    project_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_service = Depends(get_db_service)
):
    """Delete a project using Insightful-compatible endpoint."""
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        # Use existing project deletion logic from database service
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
        
        # Format response to match Insightful format
        return {
            "id": deleted_project['id'],
            "archived": not deleted_project['is_active'],
            "statuses": [],  # Would be populated from your status data
            "priorities": ["low", "medium", "high"],  # Default priorities
            "billable": deleted_project['is_billable'],
            "payroll": {
                "billRate": deleted_project['hourly_rate'],
                "overtimeBillRate": deleted_project['hourly_rate']
            },
            "name": deleted_project['name'],
            "employees": [],  # Would be populated from your employee data
            "creatorId": user_id,
            "organizationId": "",  # Would be populated from your organization data
            "teams": [],  # Would be populated from your team data
            "createdAt": int(datetime.fromisoformat(deleted_project['created_at']).timestamp() * 1000)
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error deleting project: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")

@router.delete("/task/{task_id}")
async def delete_insightful_task(
    task_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_service = Depends(get_db_service)
):
    """Delete a task using Insightful-compatible endpoint."""
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        # Use existing task deletion logic
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # First find which project the task belongs to
        cursor.execute(
            '''
            SELECT pt.id, pt.name, pt.description, pt.project_id, pt.estimated_hours,
                pt.is_active, pt.created_at, pt.updated_at, p.user_id
            FROM project_tasks pt
            JOIN projects p ON pt.project_id = p.id
            WHERE pt.id = ?
            ''',
            (task_id,)
        )
        
        row = cursor.fetchone()
        
        if not row or row[8] != user_id:
            raise HTTPException(status_code=404, detail="Task not found or not authorized")
            
        # Convert to dictionary
        column_names = [
            'id', 'name', 'description', 'project_id', 'estimated_hours',
            'is_active', 'created_at', 'updated_at', 'user_id'
        ]
        
        task_data = {
            column_names[i]: row[i] if row[i] is not None else None 
            for i in range(len(column_names))
        }
        
        # Delete the task
        cursor.execute(
            'DELETE FROM project_tasks WHERE id = ?',
            (task_id,)
        )
        
        conn.commit()
        
        logger.info(f"Deleted task {task_id}")
        
        # Format response to match Insightful format
        return {
            "id": task_data['id'],
            "status": "Done",  # Placeholder status
            "priority": "medium",  # Placeholder priority
            "billable": True,  # Default value
            "name": task_data['name'],
            "projectId": task_data['project_id'],
            "employees": [],  # Would be populated from your data
            "description": task_data['description'] or "",
            "creatorId": user_id,
            "organizationId": "",  # Would be populated from your data
            "teams": [],  # Would be populated from your data
            "createdAt": int(datetime.fromisoformat(task_data['created_at']).timestamp() * 1000)
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error deleting task: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete task: {str(e)}")

@router.get("/employee/deactivate/{employee_id}")
async def deactivate_insightful_employee(
    employee_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_service = Depends(get_db_service)
):
    """Deactivate an employee using Insightful-compatible endpoint."""
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        # Check if user has admin rights (example implementation)
        is_admin = False
        if user_id == employee_id:
            is_admin = True  # Allow self-deactivation
        else:
            # Check admin status in org_members table
            conn = db_service._get_connection()
            cursor = conn.cursor()
            
            # This query assumes you have a role field in org_members table
            cursor.execute(
                '''
                SELECT COUNT(*) FROM org_members 
                WHERE user_id = ? AND role IN ('owner', 'admin')
                ''',
                (user_id,)
            )
            
            count = cursor.fetchone()[0]
            is_admin = count > 0
        
        if not is_admin:
            raise HTTPException(status_code=403, detail="Only administrators can deactivate employees")
        
        # Mark the user as inactive in your database
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Update the user in org_members or users table 
        # This is a placeholder - adapt to your actual schema
        cursor.execute(
            '''
            UPDATE users SET is_active = 0, updated_at = ? WHERE id = ?
            ''',
            (datetime.now().isoformat(), employee_id)
        )
        
        # Get updated user data
        cursor.execute(
            '''
            SELECT id, email, name, created_at FROM users WHERE id = ?
            ''',
            (employee_id,)
        )
        
        user_data = cursor.fetchone()
        if not user_data:
            raise HTTPException(status_code=404, detail="Employee not found")
        
        # Commit changes
        conn.commit()
        
        # Format response to match Insightful format
        return {
            "id": user_data[0],
            "email": user_data[1],
            "name": user_data[2],
            "deactivated": int(datetime.now().timestamp() * 1000),
            "createdAt": int(datetime.fromisoformat(user_data[3]).timestamp() * 1000)
        }
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error deactivating employee: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to deactivate employee: {str(e)}")

@router.get("/screenshots")
async def get_insightful_screenshots(
    start: int,  # Unix timestamp in milliseconds
    end: int,    # Unix timestamp in milliseconds
    timezone: Optional[str] = None,
    task_id: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: Optional[int] = 100,
    next_token: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_service = Depends(get_db_service)
):
    """Get screenshots using Insightful-compatible endpoint."""
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        # Convert millisecond timestamps to ISO format for database query
        start_date = datetime.fromtimestamp(start / 1000).isoformat()
        end_date = datetime.fromtimestamp(end / 1000).isoformat()
        
        # Build query parameters
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Build query conditions
        query = '''
        SELECT 
            s.id, s.filepath, s.thumbnail_path, s.timestamp, s.time_entry_id, 
            s.activity_log_id, s.created_at,
            te.project_id, te.task_id, te.description,
            u.id as user_id, u.name as user_name, u.email as user_email
        FROM screenshots s
        LEFT JOIN time_entries te ON s.time_entry_id = te.id
        LEFT JOIN users u ON te.user_id = u.id
        WHERE s.timestamp BETWEEN ? AND ?
        '''
        
        params = [start_date, end_date]
        
        if task_id:
            query += ' AND te.task_id = ?'
            params.append(task_id)
            
        if project_id:
            query += ' AND te.project_id = ?'
            params.append(project_id)
        
        # Add pagination
        query += f' ORDER BY s.timestamp DESC LIMIT {limit}'
        
        # Execute query
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Format results in Insightful-style format
        results = []
        for row in cursor.fetchall():
            column_names = [
                'id', 'filepath', 'thumbnail_path', 'timestamp', 'time_entry_id',
                'activity_log_id', 'created_at', 'project_id', 'task_id', 
                'description', 'user_id', 'user_name', 'user_email'
            ]
            
            screenshot_data = {
                column_names[i]: row[i] if row[i] is not None else None 
                for i in range(len(column_names))
            }
            
            # Convert format to match Insightful
            results.append({
                "id": screenshot_data['id'],
                "type": "scheduled",
                "timestamp": int(datetime.fromisoformat(screenshot_data['timestamp']).timestamp() * 1000),
                "timezoneOffset": 0,  # Would be populated with actual timezone offset
                "app": screenshot_data['description'] or "Time Tracker",
                "title": screenshot_data['description'] or f"Time Entry {screenshot_data['time_entry_id']}",
                "projectId": screenshot_data['project_id'],
                "taskId": screenshot_data['task_id'],
                "user": screenshot_data['user_name'],
                "name": screenshot_data['user_name'],
                "employeeId": screenshot_data['user_id'],
                "createdAt": int(datetime.fromisoformat(screenshot_data['created_at']).timestamp() * 1000),
                "link": screenshot_data['filepath']
            })
        
        return {"data": results}
    except Exception as e:
        logger.error(f"Error retrieving screenshots: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve screenshots: {str(e)}")

@router.get("/time-windows")
async def get_insightful_time_windows(
    start: int,  # Unix timestamp in milliseconds
    end: int,    # Unix timestamp in milliseconds
    timezone: Optional[str] = None,
    employee_id: Optional[str] = None,
    team_id: Optional[str] = None,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    shift_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_service = Depends(get_db_service)
):
    """Get time tracking windows using Insightful-compatible endpoint."""
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        # Convert millisecond timestamps to ISO format for database query
        start_date = datetime.fromtimestamp(start / 1000).isoformat()
        end_date = datetime.fromtimestamp(end / 1000).isoformat()
        
        # Build query conditions
        query = '''
        SELECT 
            te.id, te.start_time, te.end_time, te.description,
            te.project_id, te.task_id, te.user_id,
            p.name as project_name, p.hourly_rate,
            u.name as user_name, u.email as user_email
        FROM time_entries te
        LEFT JOIN projects p ON te.project_id = p.id
        LEFT JOIN users u ON te.user_id = u.id
        WHERE te.start_time BETWEEN ? AND ?
        '''
        
        params = [start_date, end_date]
        
        # Add filters
        if employee_id:
            query += ' AND te.user_id = ?'
            params.append(employee_id)
            
        if project_id:
            query += ' AND te.project_id = ?'
            params.append(project_id)
            
        if task_id:
            query += ' AND te.task_id = ?'
            params.append(task_id)
        
        # Execute query
        conn = db_service._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        # Process results
        results = []
        for row in cursor.fetchall():
            column_names = [
                'id', 'start_time', 'end_time', 'description',
                'project_id', 'task_id', 'user_id', 'project_name',
                'hourly_rate', 'user_name', 'user_email'
            ]
            
            entry_data = {
                column_names[i]: row[i] if row[i] is not None else None 
                for i in range(len(column_names))
            }
            
            # Calculate duration in milliseconds
            start_ts = datetime.fromisoformat(entry_data['start_time']).timestamp() * 1000
            
            end_ts = None
            if entry_data['end_time']:
                end_ts = datetime.fromisoformat(entry_data['end_time']).timestamp() * 1000
            else:
                end_ts = datetime.now().timestamp() * 1000  # Ongoing entry
            
            # Format to match Insightful response
            results.append({
                "id": entry_data['id'],
                "type": "manual",
                "note": entry_data['description'] or "",
                "start": int(start_ts),
                "end": int(end_ts),
                "timezoneOffset": 0,  # Would be populated with actual offset
                "projectId": entry_data['project_id'],
                "taskId": entry_data['task_id'],
                "paid": False,
                "billable": True,
                "overtime": False,
                "billRate": float(entry_data['hourly_rate'] or 0),
                "overtimeBillRate": 0,
                "user": entry_data['user_name'],
                "name": entry_data['user_name'],
                "employeeId": entry_data['user_id'],
                "projectName": entry_data['project_name']
            })
        
        return results
    except Exception as e:
        logger.error(f"Error retrieving time windows: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve time windows: {str(e)}")

@router.get("/project-time")
async def get_insightful_project_time(
    start: int,  # Unix timestamp in milliseconds
    end: int,    # Unix timestamp in milliseconds
    timezone: Optional[str] = None,
    employee_id: Optional[str] = None,
    team_id: Optional[str] = None,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    shift_id: Optional[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db_service = Depends(get_db_service)
):
    """Get project time analytics using Insightful-compatible endpoint."""
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        # Convert millisecond timestamps to ISO format for database query
        start_date = datetime.fromtimestamp(start / 1000).isoformat()
        end_date = datetime.fromtimestamp(end / 1000).isoformat()
        
        # Build query to get time entries grouped by project
        query = '''
        SELECT 
            p.id as project_id, 
            p.name as project_name,
            SUM(CASE 
                WHEN te.end_time IS NOT NULL 
                THEN (julianday(te.end_time) - julianday(te.start_time)) * 24 * 60 * 60
                ELSE (julianday('now') - julianday(te.start_time)) * 24 * 60 * 60
                END) as total_seconds,
            COUNT(te.id) as entry_count
        FROM time_entries te
        JOIN projects p ON te.project_id = p.id
        WHERE te.start_time BETWEEN ? AND ?
        '''
        
        params = [start_date, end_date]
        
        # Add filters
        if employee_id:
            query += ' AND te.user_id = ?'
            params.append(employee_id)
            
        if project_id:
            query += ' AND te.project_id = ?'
            params.append(project_id)
            
        if task_id:
            query += ' AND te.task_id = ?'
            params.append(task_id)
        
        # Group by project
        query += ' GROUP BY p.id, p.name'
        
        # Execute query
        conn = db_service._get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        
        # Process results
        results = []
        for row in cursor.fetchall():
            project_id, project_name, total_seconds, entry_count = row
            
            # Format to match Insightful response
            results.append({
                "id": project_id,
                "name": project_name,
                "duration": int(total_seconds * 1000),  # Convert seconds to milliseconds
                "entryCount": entry_count
            })
        
        return results
    except Exception as e:
        logger.error(f"Error retrieving project time: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve project time: {str(e)}")
