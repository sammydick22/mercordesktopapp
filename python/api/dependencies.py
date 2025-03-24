"""
Dependency injection system for the Time Tracker API.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from services.supabase_auth import SupabaseAuthService
from services.improved_sync import ImprovedSupabaseSyncService
from services.database import DatabaseService

# Security scheme
security = HTTPBearer()

# Service instances (singleton pattern)
_auth_service = None
_sync_service = None
_db_service = None

def get_db_service():
    """Get database service singleton."""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service

def get_auth_service():
    """Get auth service singleton."""
    global _auth_service
    if _auth_service is None:
        _auth_service = SupabaseAuthService()
    return _auth_service

def get_sync_service():
    """Get sync service singleton."""
    global _sync_service
    if _sync_service is None:
        db_service = get_db_service()
        auth_service = get_auth_service()
        _sync_service = ImprovedSupabaseSyncService(db_service, auth_service)
    return _sync_service

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security),
                          auth_service: SupabaseAuthService = Depends(get_auth_service)):
    """
    Get the current authenticated user.
    
    This dependency enforces authentication for protected routes.
    """
    try:
        # Use the token from authorization header
        token = credentials.credentials
        auth_service.access_token = token
        
        # Verify token is valid
        if not auth_service.is_token_valid():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token or token expired",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Get user info
        user = await auth_service.get_user()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
