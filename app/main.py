from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import endpoints as api_v1
from app.core.config import settings

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

@app.get("/")
def read_root():
    return {"message": "Welcome to CritiqueWire Backend"} 