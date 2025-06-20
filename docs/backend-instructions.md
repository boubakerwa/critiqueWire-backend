# Backend Implementation Instructions for CritiqueWire API

## Objective
The goal is to build a secure, scalable, and efficient FastAPI backend service that implements the functionalities defined in the `docs/api-specification.md`. This backend will primarily handle AI-powered analysis of news articles using the OpenAI API.

## Core Requirements
1.  **Language/Framework**: Python 3.10+ with FastAPI.
2.  **Authentication**: All endpoints must be protected. Authentication will be handled by validating JWTs issued by our Supabase authentication service.
3.  **Database**: The service will be stateless and will not connect directly to the database. State is managed by the frontend and Supabase.
4.  **OpenAI Integration**: The service will integrate with the OpenAI API (GPT-4o-mini) to perform various text analysis tasks.
5.  **Configuration**: All sensitive keys and configuration variables (e.g., `OPENAI_API_KEY`, `SUPABASE_JWT_SECRET`) must be loaded from environment variables, not hardcoded. Use a `.env` file for local development.
6.  **Dependency Management**: All Python dependencies must be listed in a `requirements.txt` file.

## Project Structure
Please follow a standard FastAPI project structure. I recommend the following layout:

```
/backend
|-- /app
|   |-- /api
|   |   |-- /v1
|   |   |   |-- __init__.py
|   |   |   |-- endpoints.py      # Main API endpoints
|   |   |   |-- schemas.py        # Pydantic models for request/response
|   |   |-- __init__.py
|   |-- /core
|   |   |-- __init__.py
|   |   |-- config.py         # Configuration management
|   |   |-- security.py       # Authentication and security logic
|   |-- /services
|   |   |-- __init__.py
|   |   |-- openai_service.py # Logic for interacting with OpenAI
|   |-- __init__.py
|   |-- main.py             # FastAPI app initialization
|-- .env.example
|-- .gitignore
|-- requirements.txt
|-- Dockerfile
```

## Detailed Implementation Steps

### 1. Project Setup
- Create the project directory (`/backend`).
- Set up a Python virtual environment.
- Initialize the project structure as outlined above.
- Create a `requirements.txt` file with `fastapi`, `uvicorn`, `pydantic`, `python-dotenv`, and `openai`.

### 2. Configuration (`app/core/config.py`)
- Create a Pydantic `Settings` class to manage environment variables:
  - `OPENAI_API_KEY`: Your secret key for the OpenAI API.
  - `SUPABASE_URL`: Your Supabase project URL.
  - `SUPABASE_JWT_SECRET`: The JWT Secret from your Supabase project's API settings.
  - `API_V1_STR`: The prefix for V1 of the API (e.g., `/v1`).

### 3. Authentication (`app/core/security.py`)
- Implement a dependency (e.g., `get_current_user`) that:
  - Extracts the JWT token from the `Authorization` header.
  - Decodes and validates the token using the `SUPABASE_JWT_SECRET`. You can use the `PyJWT` library for this.
  - Raises an `HTTPException` (status code 401 or 403) if the token is invalid or missing.
  - Returns the user's ID (`sub` claim) from the token payload.

### 4. Pydantic Schemas (`app/api/v1/schemas.py`)
- Create Pydantic models for all request and response bodies as defined in `docs/api-specification.md`.
- Use inheritance to avoid repetition (e.g., a base `AnalysisOptions` model).
- This ensures strong data validation for all API interactions.

### 5. OpenAI Service (`app/services/openai_service.py`)
- Initialize the OpenAI client using the `OPENAI_API_KEY`.
- Create functions for each analysis type specified in the `Analyze Article` endpoint options in the API spec (e.g., `get_bias_analysis`, `get_fact_check`).
- Each function should take the article content/title as input and construct a specific prompt for the OpenAI API to get the desired JSON output.
- **Crucially**, use OpenAI's "JSON mode" to ensure the model returns valid JSON that can be parsed directly into your Pydantic schemas.

### 6. API Endpoints (`app/api/v1/endpoints.py`)
- Implement all endpoints as defined in `docs/api-specification.md`.
- Use the `Depends` function to protect endpoints with your authentication dependency.
- Structure your endpoints logically. Use FastAPI's `APIRouter` to group related endpoints.
- For the `POST /v1/analysis/article` endpoint, you should plan for it to be an asynchronous task. The initial response should be quick, acknowledging the request. The actual processing should happen in the background. For a simple start, a synchronous response is acceptable, but for production, this needs to be asynchronous (e.g., using Celery or FastAPI's `BackgroundTasks`).
- The `GET /v1/analysis/{analysisId}` endpoint will later be used to fetch the results of this background task. For now, it can return a mock response.

### 7. Main Application File (`app/main.py`)
- Create the main FastAPI app instance.
- Include the API router from `app/api/v1/endpoints.py`.
- Configure CORS middleware (`CORSMiddleware`) to allow requests from your frontend's domain. Make this configurable via environment variables.

### 8. Health Check
- Implement the `GET /health` endpoint. This is a simple, unauthenticated endpoint that returns a 200 status and a JSON object indicating the service is healthy. This is crucial for deployment monitoring on services like Render.

## Final Deliverables
- A fully functional FastAPI application that implements the specified endpoints.
- A `requirements.txt` file listing all dependencies.
- A `.env.example` file showing the required environment variables.
- A `Dockerfile` for containerizing the application for deployment on Render.

Please refer to `docs/api-specification.md` as the single source of truth for all endpoint paths, request/response models, and status codes. 