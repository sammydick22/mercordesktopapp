"""
Settings API routes for the Time Tracker desktop app.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from api.dependencies import get_current_user
from services.database import DatabaseService

# Setup logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    tags=["settings"],
    responses={404: {"description": "Not found"}},
)

# Create database service
db_service = DatabaseService()

# Default settings values
default_settings = {
    "screenshot_interval": 120,  # 2 minutes
    "screenshot_quality": "medium",
    "auto_sync_interval": 300,  # 5 minutes
    "idle_detection_timeout": 300,  # 5 minutes
    "theme": "system",
    "notifications_enabled": True
}

# Initialize database tables if needed
def initialize_db():
    try:
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Create user_settings table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id TEXT PRIMARY KEY,
            screenshot_interval INTEGER NOT NULL DEFAULT 120,
            screenshot_quality TEXT NOT NULL DEFAULT 'medium',
            auto_sync_interval INTEGER NOT NULL DEFAULT 300,
            idle_detection_timeout INTEGER NOT NULL DEFAULT 300,
            theme TEXT NOT NULL DEFAULT 'system',
            notifications_enabled BOOLEAN NOT NULL DEFAULT 1,
            synced BOOLEAN NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create user_profiles table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profiles (
            user_id TEXT PRIMARY KEY,
            name TEXT,
            email TEXT NOT NULL,
            timezone TEXT DEFAULT 'UTC',
            hourly_rate REAL DEFAULT 0,
            avatar_url TEXT,
            synced BOOLEAN NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        logger.info("Settings database initialized")
    except Exception as e:
        logger.error(f"Error initializing settings database: {str(e)}")

# Initialize database on startup
initialize_db()

@router.get("/settings/reset")
async def reset_settings(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Reset the settings to default values for the current user.
    
    Returns:
        The reset settings
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        
        # Update the user's settings with default values
        cursor.execute(
            '''
            UPDATE user_settings 
            SET 
                screenshot_interval = ?, 
                screenshot_quality = ?, 
                auto_sync_interval = ?,
                idle_detection_timeout = ?, 
                theme = ?, 
                notifications_enabled = ?,
                updated_at = ?
            WHERE user_id = ?
            ''',
            (
                default_settings['screenshot_interval'],
                default_settings['screenshot_quality'],
                default_settings['auto_sync_interval'],
                default_settings['idle_detection_timeout'],
                default_settings['theme'],
                1 if default_settings['notifications_enabled'] else 0,
                timestamp,
                user_id
            )
        )
        
        # If no settings were updated, create them
        if cursor.rowcount == 0:
            cursor.execute(
                '''
                INSERT INTO user_settings
                (user_id, screenshot_interval, screenshot_quality, auto_sync_interval,
                idle_detection_timeout, theme, notifications_enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    user_id,
                    default_settings['screenshot_interval'],
                    default_settings['screenshot_quality'],
                    default_settings['auto_sync_interval'],
                    default_settings['idle_detection_timeout'],
                    default_settings['theme'],
                    1 if default_settings['notifications_enabled'] else 0,
                    timestamp,
                    timestamp
                )
            )
        
        conn.commit()
        
        # Get and return the reset settings
        return await get_settings(current_user)
        
    except Exception as e:
        logger.error(f"Error resetting settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reset settings: {str(e)}")


@router.get("/settings")
async def get_settings(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the settings for the current user.
    
    Returns:
        The settings
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Check if settings exist for this user
        cursor.execute(
            'SELECT COUNT(*) FROM user_settings WHERE user_id = ?',
            (user_id,)
        )
        
        count = cursor.fetchone()[0]
        
        # If no settings exist, create default settings
        if count == 0:
            timestamp = datetime.now().isoformat()
            
            # Insert default settings
            cursor.execute(
                '''
                INSERT INTO user_settings
                (user_id, screenshot_interval, screenshot_quality, auto_sync_interval,
                idle_detection_timeout, theme, notifications_enabled, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    user_id,
                    default_settings['screenshot_interval'],
                    default_settings['screenshot_quality'],
                    default_settings['auto_sync_interval'],
                    default_settings['idle_detection_timeout'],
                    default_settings['theme'],
                    1 if default_settings['notifications_enabled'] else 0,
                    timestamp,
                    timestamp
                )
            )
            
            conn.commit()
        
        # Get user settings
        cursor.execute(
            '''
            SELECT 
                screenshot_interval, screenshot_quality, auto_sync_interval,
                idle_detection_timeout, theme, notifications_enabled
            FROM user_settings 
            WHERE user_id = ?
            ''',
            (user_id,)
        )
        
        row = cursor.fetchone()
        
        # Convert to dictionary
        column_names = [
            'screenshot_interval', 'screenshot_quality', 'auto_sync_interval',
            'idle_detection_timeout', 'theme', 'notifications_enabled'
        ]
        
        settings = {
            column_names[i]: row[i] if i != 5 else bool(row[i])  # Convert notifications_enabled to boolean
            for i in range(len(column_names))
        }
        
        return settings
        
    except Exception as e:
        logger.error(f"Error getting settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get settings: {str(e)}")

@router.put("/settings")
async def update_settings(
    settings_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update the settings for the current user.
    
    Args:
        settings_data: The settings data to update
        
    Returns:
        The updated settings
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # First ensure settings exist for this user by calling get_settings
        await get_settings(current_user)
        
        # Build SET clause for the update
        set_clauses = []
        params = []
        
        allowed_fields = [
            'screenshot_interval', 'screenshot_quality', 'auto_sync_interval',
            'idle_detection_timeout', 'theme', 'notifications_enabled'
        ]
        
        for field in allowed_fields:
            if field in settings_data:
                set_clauses.append(f"{field} = ?")
                
                # Convert boolean to integer for SQLite if needed
                if field == 'notifications_enabled':
                    params.append(1 if settings_data[field] else 0)
                else:
                    params.append(settings_data[field])
        
        # Add updated_at timestamp
        set_clauses.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        
        # Add user_id to parameters
        params.append(user_id)
        
        # Execute update if there are fields to update
        if set_clauses:
            cursor.execute(
                f'''
                UPDATE user_settings 
                SET {", ".join(set_clauses)}
                WHERE user_id = ?
                ''',
                tuple(params)
            )
            
            conn.commit()
        
        # Get the updated settings
        return await get_settings(current_user)
        
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")

@router.get("/profile")
async def get_profile(
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Get the profile for the current user.
    
    Returns:
        The profile
    """
    try:
        user_id = current_user.get("id")
        user_email = current_user.get("email")
        
        if not user_id or not user_email:
            raise HTTPException(status_code=401, detail="User ID or email not found")
        
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # Check if profile exists for this user
        cursor.execute(
            'SELECT COUNT(*) FROM user_profiles WHERE user_id = ?',
            (user_id,)
        )
        
        count = cursor.fetchone()[0]
        
        # If no profile exists, create default profile
        if count == 0:
            timestamp = datetime.now().isoformat()
            default_name = user_email.split("@")[0] if "@" in user_email else user_email
            
            # Insert default profile
            cursor.execute(
                '''
                INSERT INTO user_profiles
                (user_id, name, email, timezone, hourly_rate, avatar_url, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    user_id,
                    default_name,
                    user_email,
                    'UTC',
                    0.0,
                    None,
                    timestamp,
                    timestamp
                )
            )
            
            conn.commit()
        
        # Get user profile
        cursor.execute(
            '''
            SELECT 
                user_id, name, email, timezone, hourly_rate, avatar_url
            FROM user_profiles 
            WHERE user_id = ?
            ''',
            (user_id,)
        )
        
        row = cursor.fetchone()
        
        # Convert to dictionary
        column_names = [
            'id', 'name', 'email', 'timezone', 'hourly_rate', 'avatar_url'
        ]
        
        profile = {
            column_names[i]: row[i]
            for i in range(len(column_names))
        }
        
        return profile
        
    except Exception as e:
        logger.error(f"Error getting profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get profile: {str(e)}")

@router.put("/profile")
async def update_profile(
    profile_data: Dict[str, Any],
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """
    Update the profile for the current user.
    
    Args:
        profile_data: The profile data to update
        
    Returns:
        The updated profile
    """
    try:
        user_id = current_user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User ID not found")
        
        conn = db_service._get_connection()
        cursor = conn.cursor()
        
        # First ensure profile exists for this user by calling get_profile
        await get_profile(current_user)
        
        # Build SET clause for the update
        set_clauses = []
        params = []
        
        allowed_fields = [
            'name', 'email', 'timezone', 'hourly_rate', 'avatar_url'
        ]
        
        for field in allowed_fields:
            if field in profile_data:
                set_clauses.append(f"{field} = ?")
                params.append(profile_data[field])
        
        # Add updated_at timestamp
        set_clauses.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        
        # Add user_id to parameters
        params.append(user_id)
        
        # Execute update if there are fields to update
        if set_clauses:
            cursor.execute(
                f'''
                UPDATE user_profiles 
                SET {", ".join(set_clauses)}
                WHERE user_id = ?
                ''',
                tuple(params)
            )
            
            conn.commit()
        
        # Get the updated profile
        return await get_profile(current_user)
        
    except Exception as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")
