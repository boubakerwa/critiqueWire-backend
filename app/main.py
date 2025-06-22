from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import endpoints as api_v1
from app.core.config import settings
from app.services.scheduler_service import scheduler_service
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define common error responses for the OpenAPI schema
responses = {
    401: {"description": "Authentication failed or was not provided."},
    403: {"description": "The authenticated user is not permitted to perform this action."},
    404: {"description": "The requested resource was not found."},
    422: {"description": "Input validation failed."},
}

app = FastAPI(
    title="CritiqueWire Backend",
    responses=responses
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1.router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    """Start background services when the application starts."""
    try:
        logger.info("Starting CritiqueWire Backend services...")
        await scheduler_service.start()
        logger.info("Background scheduler started successfully")
    except Exception as e:
        logger.error(f"Failed to start background services: {e}")
        # Don't prevent the app from starting if scheduler fails
        # This allows the API to work even if RSS collection is not available

@app.on_event("shutdown")
async def shutdown_event():
    """Stop background services when the application shuts down."""
    try:
        logger.info("Stopping CritiqueWire Backend services...")
        await scheduler_service.stop()
        logger.info("Background scheduler stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping background services: {e}")

@app.get("/")
def read_root():
    return {"message": "Welcome to CritiqueWire Backend"} 