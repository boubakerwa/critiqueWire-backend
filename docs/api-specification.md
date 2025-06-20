# CritiqueWire API Specification

## Base URL
```
Production: https://api.critiquewire.com
Development: http://localhost:8000
```

## Authentication
All endpoints require authentication using a JWT Bearer token obtained from Supabase Auth. The backend will validate this token with the Supabase project.
```
Authorization: Bearer <supabase_jwt_token>
```
The backend should be configured with the Supabase URL and JWT Secret to verify incoming tokens.

## Common Response Structure
```typescript
// Success Response
{
  "status": "success",
  "data": T,  // Generic type depending on endpoint
  "timestamp": string
}

// Error Response
{
  "status": "error",
  "error": {
    "code": string,
    "message": string,
    "details": object | null
  },
  "timestamp": string
}
```

## Rate Limiting
- 100 requests per minute per user for regular endpoints
- 20 requests per minute per user for AI analysis endpoints
- Rate limit headers included in response:
  ```
  X-RateLimit-Limit: <limit>
  X-RateLimit-Remaining: <remaining>
  X-RateLimit-Reset: <timestamp>
  ```

## Endpoints

### Health Check
```http
GET /health
```
Response:
```json
{
  "status": "success",
  "data": {
    "status": "healthy",
    "version": "1.0.0"
  }
}
```

### Article Analysis

#### 1. Analyze Article
```http
POST /v1/analysis/article
```
Request:
```typescript
{
  "url": string,
  "content"?: string,  // Optional if URL is provided
  "title": string,
  "options": {
    "includeBiasAnalysis": boolean,
    "includeFactCheck": boolean,
    "includeContextAnalysis": boolean,
    "includeSummary": boolean,
    "includeExpertOpinion": boolean,
    "includeImpactAssessment": boolean
  }
}
```
Response:
```typescript
{
  "status": "success",
  "data": {
    "analysisId": string,
    "status": "processing" | "completed" | "failed",
    "estimatedTime": number  // seconds
  }
}
```

#### 2. Get Analysis Results
```http
GET /v1/analysis/{analysisId}
```
Response:
```typescript
{
  "status": "success",
  "data": {
    "analysisId": string,
    "status": "completed",
    "results": {
      "biasAnalysis"?: {
        "score": number,  // 0-1 scale
        "politicalLean": "left" | "center" | "right",
        "biasedPhrases": Array<{
          "phrase": string,
          "explanation": string,
          "suggestion": string
        }>,
        "overallAssessment": string
      },
      "factCheck"?: {
        "verifiedClaims": Array<{
          "claim": string,
          "verdict": "true" | "false" | "partially_true" | "unverified",
          "explanation": string,
          "sources": string[]
        }>,
        "reliabilityScore": number  // 0-1 scale
      },
      "contextAnalysis"?: {
        "historicalContext": string,
        "relatedEvents": Array<{
          "event": string,
          "date": string,
          "relevance": string
        }>,
        "keyStakeholders": string[]
      },
      "summary"?: {
        "executive": string,  // 2-3 sentences
        "detailed": string,   // 4-5 paragraphs
        "keyPoints": string[]
      },
      "expertOpinion"?: {
        "analysis": string,
        "credentials": string,
        "potentialBias": string,
        "alternativeViewpoints": string[]
      },
      "impactAssessment"?: {
        "socialImpact": string,
        "economicImpact": string,
        "politicalImpact": string,
        "environmentalImpact": string,
        "timeframe": "short_term" | "medium_term" | "long_term"
      }
    },
    "metadata": {
      "analyzedAt": string,
      "processingTime": number,
      "modelVersion": string,
      "confidenceScore": number
    }
  }
}
```

#### 3. Generate Follow-up Questions
```http
POST /v1/analysis/{analysisId}/questions
```
Response:
```typescript
{
  "status": "success",
  "data": {
    "questions": Array<{
      "question": string,
      "context": string,
      "type": "critical" | "exploratory" | "clarifying"
    }>
  }
}
```

### AI Reporter Chat

#### 1. Start Chat Session
```http
POST /v1/chat/sessions
```
Request:
```typescript
{
  "context"?: {
    "articleId"?: string,
    "analysisId"?: string,
    "topic"?: string
  }
}
```
Response:
```typescript
{
  "status": "success",
  "data": {
    "sessionId": string,
    "expiresAt": string
  }
}
```

#### 2. Send Message
```http
POST /v1/chat/sessions/{sessionId}/messages
```
Request:
```typescript
{
  "message": string,
  "attachments"?: Array<{
    "type": "article" | "image" | "link",
    "content": string
  }>
}
```
Response:
```typescript
{
  "status": "success",
  "data": {
    "messageId": string,
    "response": {
      "content": string,
      "sources"?: Array<{
        "title": string,
        "url": string,
        "relevance": number
      }>,
      "suggestedFollowUp"?: string[]
    }
  }
}
```

### Error Codes

| Code | Description |
|------|-------------|
| `AUTH_001` | Invalid authentication token |
| `AUTH_002` | Token expired |
| `RATE_001` | Rate limit exceeded |
| `ANAL_001` | Invalid article URL |
| `ANAL_002` | Analysis failed |
| `ANAL_003` | Invalid analysis ID |
| `CHAT_001` | Invalid session ID |
| `CHAT_002` | Session expired |
| `SERV_001` | Internal server error |
| `SERV_002` | OpenAI API error |

## Webhooks

### Analysis Completion Webhook
```http
POST {webhook_url}
```
Payload:
```typescript
{
  "event": "analysis.completed",
  "analysisId": string,
  "status": "completed" | "failed",
  "timestamp": string,
  "data"?: {
    // Same as analysis results
  }
}
```

## Security Considerations

1. **Authentication**
   - JWT tokens with short expiration
   - Refresh token rotation
   - Rate limiting per user

2. **Data Validation**
   - Input sanitization
   - URL validation
   - Content length limits
   - File size limits for attachments

3. **API Security**
   - CORS configuration
   - HTTPS only
   - Security headers
   - Request size limits

## Monitoring and Logging

All endpoints will include:
- Request ID tracking
- Performance metrics
- Error tracking
- Usage statistics
- Cost tracking for OpenAI API calls 