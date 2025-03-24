"""
Client API routes for the Time Tracker desktop app.
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

# Create database service
db_service = DatabaseService()

# Create router
router = APIRouter(
    prefix="/clients",
    tags=["clients"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def list_clients(
    limit: int = 50,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    List clients with pagination.
    
    Args:
        limit: Maximum number of clients to return
        offset: Number of clients to skip
        
    Returns:
        List of clients
    """
    # Get user ID from current user
    user_id = current_user.get('id')
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
        
    # Get clients from database with user_id filter
    result = db_service.get_clients(limit, offset, user_id=user_id)
    
    # When using database_extensions.py, we need to wrap the result in proper format
    if isinstance(result, list):
        return {
            "total": len(result),
            "clients": result
        }
    
    # When using database.py, the result is already in the correct format
    return result

@router.get("/{client_id}")
async def get_client(
    client_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get a client by ID.
    
    Args:
        client_id: The ID of the client to retrieve
        
    Returns:
        The client
    """
    # Get client from database
    client = db_service.get_client(client_id)
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    return {"client": client}

@router.post("/")
async def create_client(
    client: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Create a new client.
    
    Args:
        client: The client data
        
    Returns:
        The created client
    """
    # Get user ID from current user
    user_id = current_user.get('id')
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    # Extract name from client data
    name = client.get("name", "")
    if not name:
        raise HTTPException(status_code=400, detail="Client name is required")
    
    # Create a copy of client data without the 'name' key to avoid duplicate argument
    client_data = {k: v for k, v in client.items() if k != 'name'}
    
    # Call create_client with name as first argument, user_id as second, and remaining data as kwargs
    new_client = db_service.create_client(name, user_id, **client_data)
    
    if not new_client:
        raise HTTPException(status_code=500, detail="Failed to create client")
    
    logger.info(f"Created client {new_client['id']}")
    
    return {"client": new_client}

@router.put("/{client_id}")
async def update_client(
    client_id: str,
    client_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update a client.
    
    Args:
        client_id: The ID of the client to update
        client_data: The client data to update
        
    Returns:
        The updated client
    """
    # Update client in database
    updated_client = db_service.update_client(client_id, client_data)
    
    if not updated_client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    logger.info(f"Updated client {client_id}")
    
    return {"client": updated_client}

@router.delete("/{client_id}")
async def delete_client(
    client_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Delete a client.
    
    Args:
        client_id: The ID of the client to delete
        
    Returns:
        Success message
    """
    # Get client before deletion
    client = db_service.get_client(client_id)
    
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Delete client from database
    if not db_service.delete_client(client_id):
        raise HTTPException(status_code=500, detail="Failed to delete client")
    
    logger.info(f"Deleted client {client_id}")
    
    return {"client": client}
