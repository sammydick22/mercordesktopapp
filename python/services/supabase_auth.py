"""
Supabase authentication service for the desktop application.
"""
import logging
import os
import json
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import jwt
from supabase import create_client, Client

# Setup logger
logger = logging.getLogger(__name__)

class SupabaseAuthService:
    """
    Service for handling Supabase authentication.
    
    This service manages authentication with Supabase, including:
    - User sign-in with email/password
    - Token refresh and management
    - Session persistence
    - User profile operations
    """
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        """
        Initialize the Supabase authentication service.
        
        Args:
            supabase_url: The Supabase project URL
            supabase_key: The Supabase anon key
        """
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_ANON_KEY")
        
        # Authentication state
        self.access_token = None
        self.refresh_token = None
        self.expires_at = None
        self.user = None
        
        # Initialize Supabase client
        if self.supabase_url and self.supabase_key:
            try:
                self.supabase: Client = create_client(self.supabase_url, self.supabase_key)
                logger.info("Supabase client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase client: {str(e)}")
                self.supabase = None
        else:
            logger.warning("Supabase URL or key not provided")
            self.supabase = None
        
    async def sign_in_with_email(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign in a user with email and password.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            dict: Authentication response including tokens and user data
        """
        if not self.supabase:
            logger.error("Supabase client not initialized")
            raise Exception("Supabase client not initialized")
        
        try:
            # Use the official client for sign in
            auth_response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            # Extract data from response
            session = auth_response.session
            user = auth_response.user
            
            # Store auth data
            self.access_token = session.access_token
            self.refresh_token = session.refresh_token
            
            # Handle expires_at which might be datetime or string
            if isinstance(session.expires_at, str):
                self.expires_at = datetime.fromisoformat(session.expires_at)
            else:
                self.expires_at = session.expires_at
                
            # Handle user object based on its type
            if user:
                if hasattr(user, 'model_dump'):
                    self.user = user.model_dump()
                elif hasattr(user, '__dict__'):
                    self.user = user.__dict__
                else:
                    # Fallback to treating it as a dictionary-like object
                    self.user = dict(user)
            else:
                self.user = None
            
            return {
                "user": self.user,
                "session": {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "expires_at": self.expires_at
                }
            }
            
        except Exception as e:
            logger.error(f"Sign in error: {str(e)}")
            raise Exception(f"Authentication failed: {str(e)}")
            
    async def sign_up_with_email(self, email: str, password: str) -> Dict[str, Any]:
        """
        Sign up a new user with email and password.
        
        Args:
            email: User's email
            password: User's password
            
        Returns:
            dict: Authentication response including user data
        """
        if not self.supabase:
            logger.error("Supabase client not initialized")
            raise Exception("Supabase client not initialized")
        
        try:
            # Use the official client for sign up
            auth_response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            # Don't set auth data on sign up as user needs to confirm email first
            user = auth_response.user
            
            # Handle user object based on its type
            user_data = None
            if user:
                if hasattr(user, 'model_dump'):
                    user_data = user.model_dump()
                elif hasattr(user, '__dict__'):
                    user_data = user.__dict__
                else:
                    # Fallback to treating it as a dictionary-like object
                    user_data = dict(user)
                    
            # Handle session object based on its type
            session_data = None
            if auth_response.session:
                if hasattr(auth_response.session, 'model_dump'):
                    session_data = auth_response.session.model_dump()
                elif hasattr(auth_response.session, '__dict__'):
                    session_data = auth_response.session.__dict__
                else:
                    # Fallback to treating it as a dictionary-like object
                    session_data = dict(auth_response.session)
                    
            return {
                "user": user_data,
                "session": session_data
            }
            
        except Exception as e:
            logger.error(f"Sign up error: {str(e)}")
            raise Exception(f"Registration failed: {str(e)}")
            
    async def refresh_session(self) -> Dict[str, Any]:
        """
        Refresh the authentication session using the refresh token.
        
        Returns:
            dict: Refreshed authentication data
        """
        if not self.supabase:
            logger.error("Supabase client not initialized")
            raise Exception("Supabase client not initialized")
            
        if not self.refresh_token:
            logger.error("No refresh token available")
            raise Exception("No refresh token available")
            
        try:
            # Use the official client to refresh the session
            auth_response = self.supabase.auth.refresh_session()
            
            # Extract data from response
            session = auth_response.session
            user = auth_response.user
            
            # Store auth data
            self.access_token = session.access_token
            self.refresh_token = session.refresh_token
            
            # Handle expires_at which might be datetime or string
            if isinstance(session.expires_at, str):
                self.expires_at = datetime.fromisoformat(session.expires_at)
            else:
                self.expires_at = session.expires_at
                
            # Handle user object based on its type
            if user:
                if hasattr(user, 'model_dump'):
                    self.user = user.model_dump()
                elif hasattr(user, '__dict__'):
                    self.user = user.__dict__
                else:
                    # Fallback to treating it as a dictionary-like object
                    self.user = dict(user)
            else:
                self.user = None
            
            return {
                "user": self.user,
                "session": {
                    "access_token": self.access_token,
                    "refresh_token": self.refresh_token,
                    "expires_at": self.expires_at
                }
            }
            
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise Exception(f"Session refresh failed: {str(e)}")
            
    async def sign_out(self) -> bool:
        """
        Sign out the current user.
        
        Returns:
            bool: True if sign out was successful
        """
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return False
            
        if not self.access_token:
            logger.warning("No user is signed in")
            return True
            
        try:
            # Use the official client to sign out
            self.supabase.auth.sign_out()
            
            # Clear auth data
            self.access_token = None
            self.refresh_token = None
            self.expires_at = None
            self.user = None
            
            return True
            
        except Exception as e:
            logger.error(f"Sign out error: {str(e)}")
            return False
            
    async def get_user(self) -> Optional[Dict[str, Any]]:
        """
        Get the current authenticated user.
        
        Returns:
            dict: User data or None if not authenticated
        """
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return None
            
        if not self.access_token:
            logger.warning("No access token available")
            return None
            
        try:
            # Use the official client to get the user
            user = self.supabase.auth.get_user()
            
            if user and user.user:
                # Handle user object based on its type
                if hasattr(user.user, 'model_dump'):
                    self.user = user.user.model_dump()
                elif hasattr(user.user, '__dict__'):
                    self.user = user.user.__dict__
                else:
                    # Fallback to treating it as a dictionary-like object
                    self.user = dict(user.user)
                return self.user
            return None
            
        except Exception as e:
            logger.error(f"Get user error: {str(e)}")
            return None
            
    async def reset_password_for_email(self, email: str) -> bool:
        """
        Send a password reset email.
        
        Args:
            email: User's email
            
        Returns:
            bool: True if reset email was sent successfully
        """
        if not self.supabase:
            logger.error("Supabase client not initialized")
            return False
        
        try:
            # Use the official client to reset password
            self.supabase.auth.reset_password_for_email(email)
            return True
            
        except Exception as e:
            logger.error(f"Password reset error: {str(e)}")
            return False
            
    def is_authenticated(self) -> bool:
        """
        Check if the user is authenticated with a valid session.
        
        Returns:
            bool: True if the user is authenticated
        """
        if not self.supabase:
            return False
            
        # Check if we have an access token
        if not self.access_token:
            return False
            
        # Check if the token is expired
        if self.expires_at:
            # Handle different types for expires_at
            if isinstance(self.expires_at, datetime):
                if datetime.now() >= self.expires_at:
                    return False
            elif isinstance(self.expires_at, int):
                # If expires_at is a timestamp
                if datetime.now() >= datetime.fromtimestamp(self.expires_at):
                    return False
            elif isinstance(self.expires_at, str):
                try:
                    expiration = datetime.fromisoformat(self.expires_at)
                    if datetime.now() >= expiration:
                        return False
                except ValueError:
                    logger.error(f"Invalid expires_at format: {self.expires_at}")
                    return False
            
        return True
            
    def is_token_valid(self) -> bool:
        """
        Check if the access token is still valid.
        
        Returns:
            bool: True if the token is valid
        """
        if not self.access_token:
            return False
            
        try:
            # Check if the session is still valid in the Supabase client
            if self.supabase and self.supabase.auth.get_session():
                return True
                
            # Fallback to manual token validation if needed
            token_data = jwt.decode(
                self.access_token, 
                options={"verify_signature": False}
            )
            
            # Check if token is expired
            if "exp" in token_data:
                exp_timestamp = token_data["exp"]
                expires_at = datetime.fromtimestamp(exp_timestamp)
                
                # Refresh before actual expiration
                buffer_seconds = 60  # 1 minute buffer
                return datetime.now() < (expires_at - timedelta(seconds=buffer_seconds))
                
            return False
            
        except (jwt.PyJWTError, Exception) as e:
            logger.error(f"Token validation error: {str(e)}")
            return False
            
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        
        Returns:
            dict: Headers with authentication token
        """
        if not self.supabase or not self.access_token:
            return {
                "Content-Type": "application/json"
            }
            
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.access_token}"
        }
            
    def save_session(self, file_path: str) -> bool:
        """
        Save the current session to a file.
        
        Args:
            file_path: Path to save the session file
            
        Returns:
            bool: True if session was saved successfully
        """
        if not self.access_token or not self.refresh_token:
            logger.warning("No session to save")
            return False
            
        try:
            # Handle expires_at which might be datetime, string, int, or None
            expires_at_str = None
            if self.expires_at:
                if isinstance(self.expires_at, datetime):
                    expires_at_str = self.expires_at.isoformat()
                elif isinstance(self.expires_at, int):
                    # Convert timestamp to datetime then to string
                    expires_at_str = datetime.fromtimestamp(self.expires_at).isoformat()
                elif isinstance(self.expires_at, str):
                    expires_at_str = self.expires_at
                
            # Make user data JSON serializable
            user_data = self._prepare_json_serializable(self.user) if self.user else None
            
            session_data = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_at": expires_at_str,
                "user": user_data
            }
            
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            with open(file_path, "w") as f:
                json.dump(session_data, f)
                
            return True
            
        except Exception as e:
            logger.error(f"Error saving session: {str(e)}")
            return False
            
    def load_session(self, file_path: str) -> bool:
        """
        Load a session from a file.
        
        Args:
            file_path: Path to the session file
            
        Returns:
            bool: True if session was loaded successfully
        """
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Session file not found: {file_path}")
                return False
                
            with open(file_path, "r") as f:
                session_data = json.load(f)
                
            self.access_token = session_data.get("access_token")
            self.refresh_token = session_data.get("refresh_token")
            
            # Parse expiration time
            expires_at = session_data.get("expires_at")
            if expires_at:
                self.expires_at = datetime.fromisoformat(expires_at)
                
            self.user = session_data.get("user")
            
            # Set session in the Supabase client if it exists
            if self.supabase and self.access_token and self.refresh_token:
                try:
                    # Updated to match current Supabase API
                    self.supabase.auth.set_session(
                        access_token=self.access_token,
                        refresh_token=self.refresh_token
                    )
                except Exception as e:
                    logger.warning(f"Could not set Supabase session: {str(e)}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading session: {str(e)}")
            return False

    def _prepare_json_serializable(self, data: Any) -> Any:
        """
        Convert a data structure to be JSON serializable.
        
        Args:
            data: The data to convert
            
        Returns:
            dict: JSON serializable data
        """
        if data is None:
            return None
            
        if isinstance(data, (str, int, float, bool)):
            return data
            
        if isinstance(data, datetime):
            return data.isoformat()
            
        if isinstance(data, dict):
            return {k: self._prepare_json_serializable(v) for k, v in data.items()}
            
        if isinstance(data, list):
            return [self._prepare_json_serializable(item) for item in data]
            
        # Try to convert to dict if it's an object
        try:
            return self._prepare_json_serializable(vars(data))
        except:
            # Last resort: convert to string
            return str(data)

if __name__ == "__main__":
    # Example usage
    import asyncio
    
    async def test_auth():
        auth_service = SupabaseAuthService()
        try:
            auth_data = await auth_service.sign_in_with_email("test@example.com", "password")
            print(f"Authenticated as {auth_data['user']['email']}")
            
            # Use refresh token
            await auth_service.refresh_session()
            
            # Sign out
            await auth_service.sign_out()
            
        except Exception as e:
            print(f"Authentication failed: {str(e)}")
    
    asyncio.run(test_auth())
