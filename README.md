# CritiqueWire Backend

This repository contains the backend service for CritiqueWire, a platform for AI-powered news article analysis. The backend is built with FastAPI and integrates with the OpenAI API to provide in-depth analysis of articles, including bias detection, fact-checking, and more.

## Features

-   **Article Analysis**: Submit an article URL or content for a comprehensive analysis.
-   **AI-Powered Insights**: Utilizes OpenAI's GPT-4o-mini for high-quality text analysis.
-   **Secure**: Endpoints are protected using JWT authentication via Supabase.
-   **Scalable**: Designed to be stateless and easily containerized for deployment.

## Getting Started

### Prerequisites

-   Python 3.10+
-   An OpenAI API key
-   A Supabase project for authentication

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/critiquewire-backend.git
    cd critiquewire-backend
    ```

2.  **Create and activate a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate
    # On Windows, use: venv\Scripts\activate
    ```

3.  **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up your environment variables:**

    Create a `.env` file in the root directory by copying the example file:

    ```bash
    cp .env.example .env
    ```

    Update the `.env` file with your credentials:

    ```
    OPENAI_API_KEY="your_openai_api_key"
    SUPABASE_URL="your_supabase_project_url"
    SUPABASE_JWT_SECRET="your_supabase_jwt_secret"
    ```

### Running the Application

To start the development server, run:

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

## Docker & Render Deployment

This application is configured for deployment using Docker.

1.  **Build the Docker image:**

    ```bash
    docker build -t critiquewire-backend .
    ```

2.  **Run the Docker container:**

    ```bash
    docker run -d -p 8000:8000 --env-file .env critiquewire-backend
    ```

### Deployment on Render

This project is ready to be deployed on Render. You can connect your GitHub repository to Render and create a new "Web Service". Render will automatically detect the `Dockerfile` and build and deploy the application.

-   **Runtime**: Docker
-   **Environment Variables**: You will need to add the same environment variables from your `.env` file to the Render service configuration.

## API Documentation

The full API specification, including detailed request and response models, is available in the `docs/api-specification.md` file. The interactive API documentation (Swagger UI) is available at `http://localhost:8000/docs` when the application is running.

### Key Endpoints

-   `GET /health`: Health check for the service.
-   `POST /v1/analysis/article`: Submit an article for analysis.
-   `GET /v1/analysis/{analysisId}`: Retrieve the results of an analysis.
-   `POST /v1/chat/sessions`: Start a new chat session with the AI reporter.
-   `POST /v1/chat/sessions/{sessionId}/messages`: Send a message in a chat session.

## Authentication

All API endpoints (except `/health`) require a valid JWT from your Supabase project. The token must be included in the `Authorization` header as a Bearer token:

```
Authorization: Bearer <your_supabase_jwt>
```

## Project Structure

The project follows a standard FastAPI structure:

```
/
|-- /app
|   |-- /api/v1       # API v1 endpoints and schemas
|   |-- /core         # Configuration and security
|   |-- /services     # OpenAI integration
|   |-- main.py       # FastAPI app initialization
|-- /docs             # API specification and instructions
|-- .env.example      # Example environment variables
|-- requirements.txt  # Python dependencies
|-- README.md         # This file
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request.

## License

This project is licensed under the MIT License.
