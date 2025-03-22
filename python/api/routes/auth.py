"""
Authentication routes for the Time Tracker API.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any

from services.supabase_auth import SupabaseAuthService
from api.dependencies import get_auth_service, get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])

class UserCredentials(BaseModel):
    """User login or signup credentials."""
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    """Authentication response model."""
    user: Dict[str, Any]
    session: Dict[str, Any]

class PasswordResetRequest(BaseModel):
    """Password reset request model."""
    email: EmailStr

@router.post("/login", response_model=AuthResponse)
async def login(credentials: UserCredentials, auth_service: SupabaseAuthService = Depends(get_auth_service)):
    """
    Sign in a user with email and password.
    
    Returns user information and session data.
    """
    try:
        result = await auth_service.sign_in_with_email(credentials.email, credentials.password)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@router.post("/signup", response_model=Dict[str, Any])
async def signup(credentials: UserCredentials, auth_service: SupabaseAuthService = Depends(get_auth_service)):
    """
    Register a new user with email and password.
    
    Returns the registration result which may indicate that email confirmation is required.
    """
    try:
        result = await auth_service.sign_up_with_email(credentials.email, credentials.password)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.post("/logout")
async def logout(auth_service: SupabaseAuthService = Depends(get_auth_service),
                user: Dict[str, Any] = Depends(get_current_user)):
    """
    Sign out the current user.
    
    Requires authentication.
    """
    try:
        success = await auth_service.sign_out()
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(auth_service: SupabaseAuthService = Depends(get_auth_service)):
    """
    Refresh the authentication session.
    
    Uses the current refresh token to get a new access token.
    """
    try:
        result = await auth_service.refresh_session()
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

@router.get("/user", response_model=Dict[str, Any])
async def get_user(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get the current authenticated user.
    
    Requires authentication.
    """
    return user

@router.post("/reset-password")
async def reset_password(request: PasswordResetRequest, auth_service: SupabaseAuthService = Depends(get_auth_service)):
    """
    Send a password reset email.
    
    Does not require authentication.
    """
    try:
        success = await auth_service.reset_password_for_email(request.email)
        return {"success": success}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
