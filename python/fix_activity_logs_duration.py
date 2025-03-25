"""
Fix existing activity logs with incorrect duration values.

This script:
1. Finds activity logs with negative or extremely large duration values
2. Recalculates durations based on timestamps or sets to a safe default
3. Updates the database with corrected values
"""
import logging
import sqlite3
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_database_connection():
    """Get a connection to the SQLite database."""
    import os
    from utils.config import Config
    
    config = Config()
    db_dir = config.get("storage.database_dir")
    if not db_dir:
        db_dir = os.path.join(config.get_app_dir(), "db")
    
    db_path = os.path.join(db_dir, "timetracker.db")
    logger.info(f"Connecting to database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def find_problematic_durations(conn):
    """Find activity logs with problematic duration values."""
    cursor = conn.cursor()
    
    # Find activity logs with negative or extremely large durations
    query = """
    SELECT 
        id, window_title, process_name, start_time, end_time, duration
    FROM activity_logs 
    WHERE 
        duration < 0 OR 
        duration > 86400 OR  -- More than 24 hours
        duration IS NULL     -- Missing duration
    """
    
    cursor.execute(query)
    logs = cursor.fetchall()
    
    logger.info(f"Found {len(logs)} activity logs with problematic durations")
    return logs

def fix_activity_log_duration(conn, log):
    """Fix the duration for a single activity log."""
    try:
        # Parse timestamps
        start_time_str = log['start_time']
        end_time_str = log['end_time']
        
        # If end_time is missing, we can't calculate duration
        if not end_time_str:
            logger.warning(f"Log {log['id']} is missing end_time, setting duration to 0")
            new_duration = 0
        else:
            try:
                # Parse timestamps, handle timezone issues
                if 'Z' in start_time_str:
                    start_time_str = start_time_str.replace('Z', '+00:00')
                if 'Z' in end_time_str:
                    end_time_str = end_time_str.replace('Z', '+00:00')
                
                # Parse as ISO format
                start_time = datetime.fromisoformat(start_time_str)
                end_time = datetime.fromisoformat(end_time_str)
                
                # Calculate duration in seconds and ensure it's positive
                duration_seconds = (end_time - start_time).total_seconds()
                
                # If duration is negative, something's wrong with the timestamps
                if duration_seconds < 0:
                    logger.warning(f"Log {log['id']} has negative duration, using absolute value")
                    duration_seconds = abs(duration_seconds)
                
                # If duration is unreasonably large (> 24 hours), cap it
                if duration_seconds > 86400:
                    logger.warning(f"Log {log['id']} has excessive duration {duration_seconds}, capping at 3600")
                    duration_seconds = 3600  # Cap at 1 hour
                
                # Convert to integer for database storage
                new_duration = int(duration_seconds)
                
            except (ValueError, TypeError) as e:
                logger.error(f"Error parsing timestamps for log {log['id']}: {str(e)}")
                logger.info(f"  start_time: {start_time_str}")
                logger.info(f"  end_time: {end_time_str}")
                # Set a default value for unparseable timestamps
                new_duration = 300  # Default to 5 minutes
        
        # Update the log with the new duration
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE activity_logs SET duration = ? WHERE id = ?",
            (new_duration, log['id'])
        )
        
        logger.info(f"Fixed log {log['id']}: Old duration = {log['duration']}, New duration = {new_duration}")
        return True
    
    except Exception as e:
        logger.error(f"Error fixing log {log['id']}: {str(e)}")
        return False

def fix_all_problematic_logs():
    """Find and fix all activity logs with problematic durations."""
    conn = get_database_connection()
    
    try:
        # Start a transaction
        conn.execute("BEGIN TRANSACTION")
        
        # Find problematic logs
        logs = find_problematic_durations(conn)
        
        # Track stats
        total = len(logs)
        fixed = 0
        errors = 0
        
        # Fix each log
        for log in logs:
            result = fix_activity_log_duration(conn, log)
            if result:
                fixed += 1
            else:
                errors += 1
        
        # Commit the changes
        conn.commit()
        
        logger.info(f"Fix completed: {fixed} fixed, {errors} errors out of {total} problematic logs")
        return fixed, errors, total
    
    except Exception as e:
        logger.error(f"Transaction error: {str(e)}")
        conn.rollback()
        return 0, 0, 0
    
    finally:
        conn.close()

if __name__ == "__main__":
    logger.info("=== FIXING ACTIVITY LOGS DURATION ===")
    fixed, errors, total = fix_all_problematic_logs()
    logger.info("=== FIX COMPLETE ===")
