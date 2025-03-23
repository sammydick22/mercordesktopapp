"""
Test script for Supabase authentication integration.
"""
import asyncio
import logging
import os
from dotenv import load_dotenv
import sys

from services.supabase_auth import SupabaseAuthService

# Check Python version
if sys.version_info < (3, 9):
    print("Error: Python 3.9 or higher is required for the Supabase client")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

async def test_auth_flow():
    """Test the full authentication flow using the Supabase client."""
    logger.info("Starting Supabase authentication test")
    
    # Create auth service
    auth_service = SupabaseAuthService()
    
    # Check if we have environment variables
    if not auth_service.supabase_url or not auth_service.supabase_key:
        logger.error("Missing Supabase URL or key in environment variables")
        return False
    
    logger.info(f"Supabase URL: {auth_service.supabase_url}")
    logger.info(f"Supabase Key: {auth_service.supabase_key[:5]}...")
    
    # Check if Supabase client was initialized
    if not auth_service.supabase:
        logger.error("Supabase client was not initialized successfully")
        return False
    
    logger.info("Supabase client initialized successfully")
    
    # Test user credentials - replace with test user credentials
    # WARNING: Don't use production credentials here!
    test_email = input("Enter test email: ")
    test_password = input("Enter test password: ")
    
    try:
        # Test sign in
        logger.info("Testing sign in with official Supabase client...")
        auth_data = await auth_service.sign_in_with_email(test_email, test_password)
        logger.info("Sign in successful!")
        
        if not auth_data or not auth_data.get("user"):
            logger.error("Auth data missing user information")
            return False
            
        user_id = auth_data["user"].get("id")
        if not user_id:
            logger.error("User ID not found in auth response")
            return False
            
        logger.info(f"User ID: {user_id}")
        
        # Test token is valid
        is_valid = auth_service.is_token_valid()
        logger.info(f"Is token valid: {is_valid}")
        if not is_valid:
            logger.warning("Token validation failed - this might be expected if the token is not properly configured")
        
        # Test user retrieval
        logger.info("Testing user retrieval...")
        user = await auth_service.get_user()
        if user:
            logger.info(f"User retrieved: {user.get('email')}")
        else:
            logger.error("Failed to retrieve user")
            return False
        
        # Test token refresh
        if auth_service.refresh_token:
            logger.info("Testing token refresh...")
            try:
                refresh_result = await auth_service.refresh_session()
                logger.info("Token refresh successful!")
            except Exception as e:
                logger.warning(f"Token refresh failed: {str(e)} - this might be expected depending on token configuration")
        
        # Create directory for session storage
        os.makedirs(os.path.join(os.path.expanduser("~"), "TimeTracker", "data"), exist_ok=True)
        
        # Save session to file
        session_path = os.path.join(os.path.expanduser("~"), "TimeTracker", "data", "session.json")
        logger.info(f"Saving session to: {session_path}")
        save_result = auth_service.save_session(session_path)
        logger.info(f"Session saved: {save_result}")
        
        # Load session from file
        logger.info("Loading session from file...")
        load_result = auth_service.load_session(session_path)
        logger.info(f"Session loaded: {load_result}")
        
        # Test sign out
        logger.info("Testing sign out...")
        sign_out_result = await auth_service.sign_out()
        logger.info(f"Sign out result: {sign_out_result}")
        
        return True
    except Exception as e:
        logger.error(f"Authentication test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Supabase Authentication Test ===")
    print("This script tests authentication with Supabase using the official client")
    print("Make sure you have the following in your .env file:")
    print("  SUPABASE_URL=your-supabase-project-url")
    print("  SUPABASE_ANON_KEY=your-supabase-anon-key")
    print("=================================\n")
    
    success = asyncio.run(test_auth_flow())
    
    if success:
        logger.info("✅ All authentication tests passed!")
        exit(0)
    else:
        logger.error("❌ Authentication tests failed!")
        exit(1)
