# CritiqueWire Backend

This repository contains the backend service for CritiqueWire, a platform for AI-powered news article analysis. The backend is built with FastAPI and integrates with the OpenAI API to provide comprehensive analysis of articles, including bias detection, fact-checking, sentiment analysis, and source credibility assessment.

## 🚀 Features

### Core Analysis Capabilities
- **Unified Analysis System**: Single endpoint (`POST /v1/analyses`) supporting both URL and text content analysis
- **Async-First Processing**: Background task processing with real-time status updates
- **Database Persistence**: Full Supabase integration with PostgreSQL for analysis storage
- **Comprehensive Analysis**: Bias detection, sentiment analysis, fact-checking, claim extraction, and source credibility assessment
- **Configurable Presets**: Built-in presets (general, political, financial, scientific, opinion) with custom preset creation
- **Analysis History**: Complete history management with filtering, search, and pagination

### Advanced Features
- **Source Credibility Assessment**: Automated evaluation of news source reliability
- **Export & Share**: Multiple export formats (PDF, DOCX, HTML, JSON, CSV) with sharing capabilities
- **User Management**: Profile management and authentication via Supabase
- **Secure API**: JWT authentication with role-based access control
- **Background Processing**: Real async analysis processing with status tracking

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

### Database Setup

This application uses Supabase (PostgreSQL) for data persistence. To set up the database:

1. **Create Supabase Project**: Set up a new project at [supabase.com](https://supabase.com)

2. **Run Database Schema**: Execute the SQL schema in your Supabase SQL Editor:
   ```bash
   # Copy and paste the contents of docs/database-schema.sql
   # into your Supabase SQL Editor and run it
   ```

3. **Environment Variables**: Ensure your `.env` file includes:
   ```env
   SUPABASE_URL="your_supabase_project_url"
   SUPABASE_ANON_KEY="your_supabase_anon_key"
   SUPABASE_JWT_SECRET="your_supabase_jwt_secret"
   ```

The schema includes:
- **analyses table**: Stores all analysis results and metadata
- **Row Level Security**: Users can only access their own analyses
- **Indexes**: Optimized for fast queries and full-text search
- **Triggers**: Automatic timestamp updates

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

#### Getting a JWT Token

For development and testing, you can get a JWT token using the included utility:

1. **Using the JWT helper script:**
   ```bash
   python get_jwt.py
   ```
   This will generate a valid JWT token and save it to `tmp_jwt.txt` for testing purposes.

2. **Manual token generation:**
   - Log into your Supabase dashboard
   - Go to Authentication > Users
   - Create a user or use existing user
   - Copy the JWT token from the user details

3. **Using the token in requests:**
   ```bash
   # Load token from file
   TOKEN=$(cat tmp_jwt.txt)
   
   # Use in API calls
   curl -H "Authorization: Bearer $TOKEN" http://localhost:8000/v1/analyses
   ```

#### Authentication Flow
- The backend validates JWT tokens against Supabase
- User information is extracted from the token payload
- Row Level Security ensures users only access their own data
- All database operations are scoped to the authenticated user

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

## 🔧 Recent Improvements

### Database Integration & Validation Fixes (June 2025)

**Fixed Critical Response Validation Issues:**
- ✅ Resolved `analysisType` field validation errors in GET `/v1/analyses/{analysis_id}`
- ✅ Fixed metadata schema compliance (`processingTime` field mapping)
- ✅ Implemented missing `create_analysis` method in database service
- ✅ Ensured proper content type detection ("url" vs "text")

**Enhanced Database Service:**
- Complete Supabase integration with proper JWT authentication
- Consistent field naming between storage and retrieval
- Proper error handling and logging for debugging
- Row-level security implementation

**Async Analysis Flow:**
- Full async analysis creation and retrieval
- Proper status tracking ("pending", "completed", "failed")
- Metadata preservation across create/retrieve operations

### Troubleshooting Common Issues

**Response Validation Errors:**
```bash
# If you see "Input should be 'url' or 'text'" errors:
# This was fixed by ensuring analysisType returns content type, not analysis types list
```

**Authentication Issues:**
```bash
# Generate fresh JWT token
python get_jwt.py

# Test authentication
curl -H "Authorization: Bearer $(cat tmp_jwt.txt)" http://localhost:8000/v1/analyses
```

**Database Connection Issues:**
```bash
# Check environment variables
cat .env | grep SUPABASE

# Test database connectivity in Python
python -c "from app.core.config import supabase_client; print(supabase_client.table('analyses').select('*').limit(1).execute())"
```

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
│   │   ├── database_service.py  # Supabase database operations
│   │   ├── openai_service.py    # OpenAI API integration
│   │   └── background_service.py # Async task processing
│   └── main.py           # FastAPI app initialization
├── docs/                 # API documentation and specifications
│   ├── api-specification.md
│   ├── backend-instructions.md
│   └── openapi_refinement_v*.md  # API evolution documentation
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker configuration
├── TODO.md              # Development roadmap and priorities
├── get_jwt.py           # JWT token generator for testing
├── tmp_jwt.txt          # Generated JWT token (for testing)
└── README.md            # This file
```

## 🧪 Testing the API

### Quick Health Check
```bash
curl http://localhost:8000/v1/health
```

### Test Authentication
```bash
# Generate JWT token
python get_jwt.py

# Test authenticated endpoint
curl -H "Authorization: Bearer $(cat tmp_jwt.txt)" \
     http://localhost:8000/v1/analyses
```

### Test Complete Analysis Flow
```bash
# 1. Create analysis (async)
curl -X POST "http://localhost:8000/v1/analyses" \
  -H "Authorization: Bearer $(cat tmp_jwt.txt)" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Sample article content for analysis...",
    "title": "Test Analysis",
    "preset": "general",
    "options": {
      "includeBiasAnalysis": true,
      "includeFactCheck": true,
      "includeExecutiveSummary": true
    },
    "async_mode": true
  }'

# 2. Retrieve analysis (use the analysisId from step 1)
curl -H "Authorization: Bearer $(cat tmp_jwt.txt)" \
     "http://localhost:8000/v1/analyses/{analysis_id}"
```

### Test URL Analysis
```bash
curl -X POST "http://localhost:8000/v1/analyses" \
  -H "Authorization: Bearer $(cat tmp_jwt.txt)" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/news-article",
    "title": "URL Analysis Test",
    "preset": "political",
    "async_mode": true
  }'
```

### Verify Database Integration
```bash
# Test that analyses are properly stored and retrieved
# Create multiple analyses and test filtering/pagination
curl -H "Authorization: Bearer $(cat tmp_jwt.txt)" \
     "http://localhost:8000/v1/analyses?limit=10&preset=general"
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
- **Full database integration with Supabase (v0.5)**
- **Fixed all response validation errors and schema compliance**
- **JWT authentication with row-level security**
- **Background task processing for async analyses**
- **Complete create/retrieve analysis flow with proper error handling**
- **Metadata field mapping and consistency fixes**

### 🔄 In Progress
- URL content extraction improvements
- Production background task system (Celery/Redis)
- WebSocket implementation for real-time updates

### 📋 Planned
- Caching and performance optimization
- Production deployment setup
- Enhanced analysis features

## 🤝 Contributing

Contributions are welcome! Please check the `TODO.md` file for current priorities and development roadmap.

## 📄 License

This project is licensed under the MIT License.
