"""
Authentication service for managing user authentication with Supabase.
"""
import logging
import os
import json
import base64
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from utils.config import Config

# Setup logger
logger = logging.getLogger(__name__)

class AuthService:
    """
    Service for managing authentication with Supabase.
    
    Handles user signup, login, token management, and session validation.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """
        Initialize the authentication service.
        
        Args:
            config: Optional configuration object. If None, creates a new one.
        """
        self.config = config or Config()
        
        # Get API URL from config
        self.api_url = self.config.get("api.url", "https://api.example.com")
        
        # Initialize state
        self.access_token = self.config.get("auth.access_token")
        self.refresh_token = self.config.get("auth.refresh_token")
        self.token_expiry = self._parse_datetime(self.config.get("auth.token_expiry"))
        self.user = self.config.get("user", {})
        
        # Token refresh lock
        self.refresh_lock = asyncio.Lock()
        
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Log in a user with email and password.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            dict: User information
            
        Raises:
            Exception: If login fails
        """
        try:
            # Prepare login request
            login_url = f"{self.api_url}/auth/v1/token?grant_type=password"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    login_url,
                    headers={
                        "Content-Type": "application/json",
                        "apikey": self.config.get("api.anon_key", "")
                    },
                    json={
                        "email": email,
                        "password": password
                    }
                ) as response:
                    if response.status != 200:
                        error_body = await response.text()
                        logger.error(f"Login failed: {error_body}")
                        raise Exception(f"Login failed: {response.status}")
                        
                    # Parse response
                    auth_data = await response.json()
                    
                    # Extract tokens
                    self.access_token = auth_data.get("access_token")
                    self.refresh_token = auth_data.get("refresh_token")
                    expires_in = auth_data.get("expires_in", 3600)
                    
                    # Calculate expiry time
                    self.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
                    
                    # Get user from token
                    user = self._decode_jwt(self.access_token)
                    
                    # Get user details
                    user_data = await self._get_user_details(user.get("sub"))
                    
                    # Store user and tokens
                    self.user = user_data
                    await self._save_auth_data()
                    
                    logger.info(f"User logged in: {user_data.get('email')}")
                    
                    return user_data
                    
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            raise
            
    async def signup(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign up a new user with email and password.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            dict: User information
            
        Raises:
            Exception: If signup fails
        """
        try:
            # Prepare signup request
            signup_url = f"{self.api_url}/auth/v1/signup"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    signup_url,
                    headers={
                        "Content-Type": "application/json",
                        "apikey": self.config.get("api.anon_key", "")
                    },
                    json={
                        "email": email,
                        "password": password
                    }
                ) as response:
                    if response.status != 200:
                        error_body = await response.text()
                        logger.error(f"Signup failed: {error_body}")
                        raise Exception(f"Signup failed: {response.status}")
                        
                    # Parse response
                    auth_data = await response.json()
                    
                    # Check if email confirmation is required
                    if not auth_data.get("access_token"):
                        return {
                            "id": auth_data.get("id"),
                            "email": email,
                            "email_confirmed": False,
                            "message": "Email confirmation required"
                        }
                    
                    # Extract tokens
                    self.access_token = auth_data.get("access_token")
                    self.refresh_token = auth_data.get("refresh_token")
                    expires_in = auth_data.get("expires_in", 3600)
                    
                    # Calculate expiry time
                    self.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
                    
                    # Get user from token
                    user = self._decode_jwt(self.access_token)
                    
                    # Get user details
                    user_data = await self._get_user_details(user.get("sub"))
                    
                    # Store user and tokens
                    self.user = user_data
                    await self._save_auth_data()
                    
                    logger.info(f"User signed up: {user_data.get('email')}")
                    
                    return user_data
                    
        except Exception as e:
            logger.error(f"Error during signup: {str(e)}")
            raise
            
    async def logout(self) -> bool:
        """
        Log out the current user.
        
        Returns:
            bool: True if logout was successful
        """
        try:
            if not self.access_token:
                logger.warning("No user logged in")
                return True
                
            # Prepare logout request
            logout_url = f"{self.api_url}/auth/v1/logout"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    logout_url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.access_token}"
                    }
                ) as response:
                    # Even if the request fails, we'll clear local auth data
                    if response.status != 200:
                        logger.warning(f"Logout API call failed: {response.status}")
                    
                    # Clear auth data
                    self.access_token = None
                    self.refresh_token = None
                    self.token_expiry = None
                    self.user = {}
                    
                    # Save cleared auth data
                    await self._save_auth_data()
                    
                    logger.info("User logged out")
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
            
            # Clear auth data anyway
            self.access_token = None
            self.refresh_token = None
            self.token_expiry = None
            self.user = {}
            
            await self._save_auth_data()
            
            return True
            
    def is_authenticated(self) -> bool:
        """
        Check if the user is authenticated.
        
        Returns:
            bool: True if authenticated
        """
        if not self.access_token or not self.token_expiry:
            return False
            
        # Check if token is expired
        if datetime.utcnow() >= self.token_expiry:
            return False
            
        return True
        
    def get_user(self) -> Dict[str, Any]:
        """
        Get the current user.
        
        Returns:
            dict: User information
        """
        return self.user
        
    async def get_access_token(self) -> Optional[str]:
        """
        Get a valid access token, refreshing if necessary.
        
        Returns:
            str: Access token or None if not authenticated
        """
        if not self.access_token:
            return None
            
        # Check if token needs refreshing
        if self.token_expiry and datetime.utcnow() >= self.token_expiry - timedelta(minutes=5):
            # Token is expired or will expire soon, refresh it
            async with self.refresh_lock:
                # Check again in case another thread refreshed while we were waiting
                if self.token_expiry and datetime.utcnow() >= self.token_expiry - timedelta(minutes=5):
                    success = await self._refresh_token()
                    if not success:
                        logger.error("Failed to refresh token")
                        return None
                        
        return self.access_token
        
    async def _refresh_token(self) -> bool:
        """
        Refresh the access token using the refresh token.
        
        Returns:
            bool: True if refresh was successful
        """
        try:
            if not self.refresh_token:
                logger.warning("No refresh token available")
                return False
                
            # Prepare refresh request
            refresh_url = f"{self.api_url}/auth/v1/token?grant_type=refresh_token"
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    refresh_url,
                    headers={
                        "Content-Type": "application/json",
                        "apikey": self.config.get("api.anon_key", "")
                    },
                    json={
                        "refresh_token": self.refresh_token
                    }
                ) as response:
                    if response.status != 200:
                        error_body = await response.text()
                        logger.error(f"Token refresh failed: {error_body}")
                        return False
                        
                    # Parse response
                    auth_data = await response.json()
                    
                    # Extract tokens
                    self.access_token = auth_data.get("access_token")
                    self.refresh_token = auth_data.get("refresh_token")
                    expires_in = auth_data.get("expires_in", 3600)
                    
                    # Calculate expiry time
                    self.token_expiry = datetime.utcnow() + timedelta(seconds=expires_in)
                    
                    # Save updated auth data
                    await self._save_auth_data()
                    
                    logger.info("Access token refreshed")
                    
                    return True
                    
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            return False
            
    async def _get_user_details(self, user_id: str) -> Dict[str, Any]:
        """
        Get user details from Supabase.
        
        Args:
            user_id: User ID
            
        Returns:
            dict: User details
        """
        try:
            # Prepare user details request
            user_url = f"{self.api_url}/auth/v1/user"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    user_url,
                    headers={
                        "Authorization": f"Bearer {self.access_token}"
                    }
                ) as response:
                    if response.status != 200:
                        error_body = await response.text()
                        logger.error(f"Get user details failed: {error_body}")
                        
                        # Fallback to basic user info
                        return {
                            "id": user_id,
                            "email": "unknown"
                        }
                        
                    # Parse response
                    user_data = await response.json()
                    
                    return {
                        "id": user_data.get("id"),
                        "email": user_data.get("email"),
                        "name": user_data.get("user_metadata", {}).get("name"),
                        "created_at": user_data.get("created_at"),
                        "last_sign_in_at": user_data.get("last_sign_in_at")
                    }
                    
        except Exception as e:
            logger.error(f"Error getting user details: {str(e)}")
            
            # Fallback to basic user info
            return {
                "id": user_id,
                "email": "unknown"
            }
            
    async def _save_auth_data(self) -> None:
        """Save authentication data to config."""
        # Save tokens
        self.config.set("auth.access_token", self.access_token)
        self.config.set("auth.refresh_token", self.refresh_token)
        self.config.set("auth.token_expiry", self._format_datetime(self.token_expiry))
        
        # Save user
        self.config.set("user", self.user)
        
    def _decode_jwt(self, token: str) -> Dict[str, Any]:
        """
        Decode a JWT token.
        
        Args:
            token: JWT token
            
        Returns:
            dict: Decoded token
        """
        if not token:
            return {}
            
        try:
            # Split the token
            token_parts = token.split('.')
            if len(token_parts) != 3:
                return {}
                
            # Decode the payload
            payload = token_parts[1]
            payload += '=' * (-len(payload) % 4)  # Add padding
            decoded = base64.b64decode(payload)
            
            return json.loads(decoded)
            
        except Exception as e:
            logger.error(f"Error decoding JWT: {str(e)}")
            return {}
            
    def _parse_datetime(self, dt_str: Optional[str]) -> Optional[datetime]:
        """
        Parse datetime string to datetime object.
        
        Args:
            dt_str: Datetime string
            
        Returns:
            datetime: Parsed datetime or None
        """
        if not dt_str:
            return None
            
        try:
            return datetime.fromisoformat(dt_str)
        except ValueError:
            return None
            
    def _format_datetime(self, dt: Optional[datetime]) -> Optional[str]:
        """
        Format datetime object to string.
        
        Args:
            dt: Datetime
            
        Returns:
            str: Formatted datetime string or None
        """
        if not dt:
            return None
            
        return dt.isoformat()
