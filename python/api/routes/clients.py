"""
Client API routes for the Time Tracker desktop app.
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
    prefix="/clients",
    tags=["clients"],
    responses={404: {"description": "Not found"}},
)

# Temporary placeholder for client data
# In the real implementation, this will use Supabase
clients = []

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
    start = offset
    end = offset + limit
    
    return {
        "total": len(clients),
        "clients": clients[start:end]
    }

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
    for client in clients:
        if client["id"] == client_id:
            return {"client": client}
    
    raise HTTPException(status_code=404, detail="Client not found")

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
    now = datetime.utcnow().isoformat()
    
    # Create new client
    new_client = {
        "id": str(uuid.uuid4()),
        "name": client.get("name"),
        "contact_name": client.get("contact_name"),
        "email": client.get("email"),
        "phone": client.get("phone"),
        "address": client.get("address"),
        "notes": client.get("notes"),
        "is_active": True,
        "created_at": now,
        "updated_at": now
    }
    
    # Store the client
    clients.append(new_client)
    
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
    for client in clients:
        if client["id"] == client_id:
            # Update client fields
            for key, value in client_data.items():
                if key in client:
                    client[key] = value
            
            # Update the updated_at timestamp
            client["updated_at"] = datetime.utcnow().isoformat()
            
            logger.info(f"Updated client {client_id}")
            
            return {"client": client}
    
    raise HTTPException(status_code=404, detail="Client not found")

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
    for i, client in enumerate(clients):
        if client["id"] == client_id:
            # Remove the client
            deleted_client = clients.pop(i)
            
            logger.info(f"Deleted client {client_id}")
            
            return {"client": deleted_client}
    
    raise HTTPException(status_code=404, detail="Client not found")
