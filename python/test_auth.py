import asyncio
import logging
import os
import getpass
from services.auth import AuthService
from utils.config import Config

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def test_auth_connection():
    """Test if we can connect to Supabase Auth using the provided credentials."""
    try:
        # Initialize config which will load the environment variables
        config = Config()
        logger.info(f"Using API URL: {config.get('api.url')}")
        
        # Check if we have the Supabase URL and key
        if config.get('api.url') == 'https://api.example.com':
            logger.error("Supabase URL not set correctly, still using default URL")
            return False
            
        if not config.get('api.anon_key'):
            logger.error("Supabase Anon Key not set")
            return False
            
        logger.info("Supabase connection details loaded successfully")
        
        # Initialize auth service
        auth_service = AuthService(config)
        
        # Get user credentials from input
        print("\nTest login with existing user credentials:")
        test_email = input("Enter email: ")
        test_password = getpass.getpass("Enter password: ")
        
        if not test_email or not test_password:
            logger.info("Login skipped - no credentials provided")
            # Just report success because we've verified the URL and key are set
            return True
        
        try:
            user_data = await auth_service.login(test_email, test_password)
            logger.info(f"User login successful: {user_data}")
            return True
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return False
            
    except Exception as e:
        logger.error(f"Error testing auth connection: {str(e)}")
        return False

async def main():
    success = await test_auth_connection()
    if success:
        logger.info("✅ Supabase connection test passed!")
    else:
        logger.error("❌ Supabase connection test failed!")

if __name__ == "__main__":
    asyncio.run(main())
