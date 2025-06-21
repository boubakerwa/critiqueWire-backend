# CritiqueWire Backend

This repository contains the backend service for CritiqueWire, a platform for AI-powered news article analysis. The backend is built with FastAPI and integrates with the OpenAI API to provide comprehensive analysis of articles, including bias detection, fact-checking, sentiment analysis, and source credibility assessment.

## 🚀 Features

### Core Analysis Capabilities
- **Unified Analysis System**: Single endpoint (`POST /v1/analyses`) supporting both URL and text content analysis
- **Async-First Processing**: Background task processing with real-time status updates
- **Comprehensive Analysis**: Bias detection, sentiment analysis, fact-checking, claim extraction, and source credibility assessment
- **Configurable Presets**: Built-in presets (general, political, financial, scientific, opinion) with custom preset creation
- **Analysis History**: Complete history management with filtering, search, and pagination

### Advanced Features
- **Source Credibility Assessment**: Automated evaluation of news source reliability
- **Export & Share**: Multiple export formats (PDF, DOCX, HTML, JSON, CSV) with sharing capabilities
- **User Management**: Profile management and authentication via Supabase
- **Secure API**: JWT authentication with role-based access control

## 🛠️ Getting Started

### Prerequisites

- Python 3.9+
- OpenAI API key
- Supabase project for authentication

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/boubakerwa/critiqueWire-backend.git
   cd critiqueWire-backend
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate
   # On Windows, use: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the root directory:
   ```bash
   cp .env.example .env
   ```
   
   Update with your credentials:
   ```env
   OPENAI_API_KEY="your_openai_api_key"
   SUPABASE_URL="your_supabase_project_url"
   SUPABASE_JWT_SECRET="your_supabase_jwt_secret"
   ```

### Running the Application

Start the development server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

## 📚 API Documentation

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

#### Analysis Endpoints
- `POST /v1/analyses` - Unified analysis endpoint (async by default)
- `GET /v1/analyses/{analysis_id}` - Retrieve analysis results (new format)
- `GET /v1/analyses` - Get analysis history with filtering and pagination
- `POST /v1/analyses/{analysis_id}/export` - Export analysis results
- `POST /v1/analyses/{analysis_id}/share` - Share analysis results

#### Source Credibility
- `POST /v1/source-credibility` - Assess source credibility

#### Analysis Presets
- `GET /v1/analysis-presets` - Get available analysis presets
- `POST /v1/analysis-presets` - Create custom analysis preset

#### User Management
- `GET /v1/profile` - Get user profile
- `PATCH /v1/profile` - Update user profile

#### Legacy Endpoints (for backward compatibility)
- `POST /v1/analysis/article/sync` - Synchronous analysis
- `POST /v1/analysis/article` - Asynchronous analysis (legacy)
- `GET /v1/analysis/{analysis_id}` - Retrieve results (legacy format)

### Authentication

All API endpoints (except `/health`) require a valid JWT from Supabase. Include the token in the `Authorization` header:

```
Authorization: Bearer <your_supabase_jwt>
```

### Example Usage

#### Quick Analysis (Synchronous)
```bash
curl -X POST "http://localhost:8000/v1/analyses" \
  -H "Authorization: Bearer <your_jwt>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your article content here...",
    "title": "Article Title",
    "preset": "general",
    "async_mode": false
  }'
```

#### Comprehensive Analysis (Asynchronous)
```bash
curl -X POST "http://localhost:8000/v1/analyses" \
  -H "Authorization: Bearer <your_jwt>" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/article",
    "title": "Article Title",
    "preset": "political",
    "options": {
      "includeBiasAnalysis": true,
      "includeSentimentAnalysis": true,
      "includeFactCheck": true,
      "includeClaimExtraction": true,
      "includeSourceCredibility": true,
      "includeExecutiveSummary": true
    },
    "async_mode": true
  }'
```

## 🐳 Docker & Deployment

### Local Docker
```bash
# Build the image
docker build -t critiquewire-backend .

# Run the container
docker run -d -p 8000:8000 --env-file .env critiquewire-backend
```

### Render Deployment
This project is configured for Render deployment:
- **Runtime**: Docker
- **Environment Variables**: Add your `.env` variables to Render service configuration
- **Auto-deploy**: Connect your GitHub repository for automatic deployments

## 📁 Project Structure

```
critiqueWire-backend/
├── app/
│   ├── api/v1/           # API v1 endpoints and schemas
│   │   ├── endpoints.py  # All API endpoints
│   │   └── schemas.py    # Pydantic models and validation
│   ├── core/             # Configuration and security
│   │   ├── config.py     # App configuration
│   │   └── security.py   # JWT authentication
│   ├── services/         # External service integrations
│   │   └── openai_service.py  # OpenAI API integration
│   └── main.py           # FastAPI app initialization
├── docs/                 # API documentation and specifications
│   ├── api-specification.md
│   ├── backend-instructions.md
│   └── openapi_refinement_v*.md  # API evolution documentation
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── TODO.md              # Development roadmap and priorities
└── README.md            # This file
```

## 🔄 API Evolution

This backend has evolved through multiple iterations:

- **v0.2**: Comprehensive analysis system with presets and history
- **v0.3**: Unified async-first analysis endpoint
- **v0.4**: API consistency improvements and standardization

See `docs/openapi_refinement_v*.md` for detailed evolution history.

## 🚧 Development Status

### ✅ Completed
- Unified analysis endpoint with async/sync modes
- Comprehensive analysis features (bias, sentiment, fact-checking)
- Source credibility assessment
- Analysis history and presets management
- Export and share functionality
- API consistency and standardization (v0.4)

### 🔄 In Progress
- Background task system (Celery/Redis)
- Database integration (PostgreSQL)
- Real-time status updates (WebSocket)

### 📋 Planned
- URL content extraction improvements
- Caching and performance optimization
- Production deployment setup

## 🤝 Contributing

Contributions are welcome! Please check the `TODO.md` file for current priorities and development roadmap.

## 📄 License

This project is licensed under the MIT License.
