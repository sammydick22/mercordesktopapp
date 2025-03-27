"""
Main FastAPI application for the Time Tracker desktop app.
"""
import os
import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(os.path.expanduser("~"), "TimeTracker", "logs", "app.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Time Tracker API",
    description="Local API for Time Tracker desktop application",
    version="1.0.0"
)

# Add CORS middleware for Electron frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "electron://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Time Tracker API is running"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}

# Import and include routers
from api.routes import time_entries, screenshots, auth, sync, clients, projects, settings, organizations, insightful

# Include routers
app.include_router(time_entries.router)
app.include_router(screenshots.router)
app.include_router(auth.router)
app.include_router(sync.router)
app.include_router(clients.router)
app.include_router(projects.router)
app.include_router(settings.router)
app.include_router(organizations.router)
app.include_router(insightful.router)

@app.on_event("startup")
async def startup_event():
    """Initialize necessary components on startup"""
    logger.info("Starting Time Tracker API")
    
    # Ensure required directories exist
    os.makedirs(os.path.join(os.path.expanduser("~"), "TimeTracker", "screenshots"), exist_ok=True)
    os.makedirs(os.path.join(os.path.expanduser("~"), "TimeTracker", "logs"), exist_ok=True)
    os.makedirs(os.path.join(os.path.expanduser("~"), "TimeTracker", "data"), exist_ok=True)
    
    # Apply database extensions and patches
    from utils.patch_loader import apply_patches_to_class
    from services.database import DatabaseService
    
    # Apply database extensions for project task sync
    apply_patches_to_class(DatabaseService, "database_extensions_patch")
    
    # Initialize services
    from api.dependencies import get_auth_service, get_sync_service, get_activity_service
    auth_service = get_auth_service()
    sync_service = get_sync_service()
    activity_service = get_activity_service()
    
    # Initialize sync service
    try:
        await sync_service.initialize()
        logger.info("Sync service initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing sync service: {str(e)}")
        
    # Initialize activity tracking service
    try:
        activity_service.start()
        logger.info("Activity tracking service started successfully")
    except Exception as e:
        logger.error(f"Error starting activity tracking service: {str(e)}")
    
    logger.info("Time Tracker API started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on shutdown"""
    logger.info("Shutting down Time Tracker API")
    
    # Stop the activity tracking service
    try:
        from api.dependencies import get_activity_service
        activity_service = get_activity_service()
        activity_service.stop()
        logger.info("Activity tracking service stopped")
    except Exception as e:
        logger.error(f"Error stopping activity tracking service: {str(e)}")

# Main execution
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
