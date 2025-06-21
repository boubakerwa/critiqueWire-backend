# OpenAPI Specification Refinement (v0.1)

This document outlines recommended refinements to the CritiqueWire backend OpenAPI specification. The suggestions are based on a review from a frontend development perspective to ensure smooth integration, a robust user experience, and a clear contract between the client and server.

## 1. Strongly-Typed Analysis Results

The most critical refinement is to provide a specific schema for the `results` object within the `AnalysisResultsResponse`. A well-defined structure is essential for the frontend to parse and display analysis data reliably.

### Suggested Schema Additions

We recommend replacing the generic `results` object with a reference to a new `AnalysisResultTypes` schema. This new schema will contain optional fields for each type of analysis.

Here are the proposed additions to the `components.schemas` section of your OpenAPI document.

```json
// ... inside components.schemas ...

"AnalysisResultsData": {
    "properties": {
        "analysisId": {
            "type": "string",
            "title": "Analysisid"
        },
        "status": {
            "type": "string",
            "const": "completed",
            "title": "Status"
        },
        "results": {
            "$ref": "#/components/schemas/AnalysisResultTypes"
        },
        "metadata": {
            "additionalProperties": true,
            "type": "object",
            "title": "Metadata"
        }
    },
    "type": "object",
    "required": [
        "analysisId",
        "status",
        "results",
        "metadata"
    ],
    "title": "AnalysisResultsData"
},

"AnalysisResultTypes": {
    "title": "AnalysisResultTypes",
    "type": "object",
    "properties": {
        "biasAnalysis": {
            "$ref": "#/components/schemas/BiasAnalysisResult"
        },
        "factCheck": {
            "$ref": "#/components/schemas/FactCheckResult"
        },
        "contextAnalysis": {
            "$ref": "#/components/schemas/ContextAnalysisResult"
        },
        "summary": {
            "$ref": "#/components/schemas/SummaryResult"
        },
        "expertOpinion": {
            "$ref": "#/components/schemas/ExpertOpinionResult"
        },
        "impactAssessment": {
            "$ref": "#/components/schemas/ImpactAssessmentResult"
        }
    },
    "description": "Contains results for the requested analysis types. A key is only present if its corresponding option was true in the request."
},

"BiasAnalysisResult": {
    "type": "object",
    "properties": {
        "score": {
            "type": "number",
            "format": "float",
            "description": "A score from 0.0 (neutral) to 1.0 (highly biased)."
        },
        "leaning": {
            "type": "string",
            "enum": ["left", "center-left", "center", "center-right", "right"],
            "description": "The detected political leaning of the content."
        },
        "summary": {
            "type": "string",
            "description": "A brief summary of the bias findings."
        },
        "details": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "quote": {"type": "string"},
                    "explanation": {"type": "string"}
                },
                "required": ["quote", "explanation"]
            },
            "description": "Specific examples from the text that indicate bias."
        }
    },
    "required": ["score", "leaning", "summary"]
},

"FactCheckResult": {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": { "type": "string", "description": "The claim extracted from the article." },
                    "verdict": { "type": "string", "enum": ["verified", "unverified", "false", "misleading"], "description": "The verdict on the claim's accuracy." },
                    "source": { "type": "string", "format": "uri", "description": "A URL to a source validating the verdict." },
                    "explanation": { "type": "string", "description": "A brief explanation of the fact-check." }
                },
                "required": ["claim", "verdict"]
            }
        }
    },
    "required": ["claims"]
},

"ContextAnalysisResult": {
    "type": "object",
    "properties": {
        "historicalBackground": { "type": "string", "description": "Historical context relevant to the article's topic." },
        "relatedEvents": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": { "type": "string" },
                    "url": { "type": "string", "format": "uri" },
                    "summary": { "type": "string" }
                },
                "required": ["title", "url"]
            },
            "description": "Links to articles about related events."
        }
    },
    "required": ["historicalBackground"]
},

"SummaryResult": {
    "type": "object",
    "properties": {
        "text": { "type": "string", "description": "A concise summary of the article." },
        "keyPoints": {
            "type": "array",
            "items": { "type": "string" },
            "description": "A list of bullet points highlighting the key takeaways."
        }
    },
    "required": ["text", "keyPoints"]
},

"ExpertOpinionResult": {
    "type": "object",
    "properties": {
        "opinions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "expertName": { "type": "string" },
                    "field": { "type": "string", "description": "The expert's field of expertise." },
                    "opinion": { "type": "string", "description": "The expert's opinion on the topic." },
                    "source": { "type": "string", "format": "uri", "description": "A URL to the source of the opinion."}
                },
                "required": ["expertName", "field", "opinion"]
            }
        }
    },
    "required": ["opinions"]
},

"ImpactAssessmentResult": {
    "type": "object",
    "properties": {
        "potentialImpact": { "type": "string", "description": "Analysis of the potential societal, economic, or political impact." },
        "affectedGroups": {
            "type": "array",
            "items": { "type": "string" },
            "description": "A list of groups or sectors that may be affected."
        }
    },
    "required": ["potentialImpact"]
}
```

## 2. New User-Specific Endpoints

To support core application features like saving articles and viewing history, the API needs endpoints that are scoped to the authenticated user.

### Suggested New Paths and Schemas

Here are definitions for the proposed new endpoints and their associated schemas. These would be added to the `paths` and `components.schemas` sections, respectively.

```json
// ... inside paths ...

"/v1/bookmarks": {
    "get": {
        "summary": "List User Bookmarks",
        "description": "Retrieves a list of all articles bookmarked by the authenticated user.",
        "operationId": "list_user_bookmarks_v1_bookmarks_get",
        "tags": ["User Data"],
        "security": [{"HTTPBearer": []}],
        "responses": {
            "200": {
                "description": "A list of bookmarks.",
                "content": { "application/json": { "schema": { "type": "array", "items": { "$ref": "#/components/schemas/Bookmark" }}}}
            },
            "401": { "$ref": "#/components/responses/UnauthorizedError" }
        }
    },
    "post": {
        "summary": "Create Bookmark",
        "description": "Adds an article to the user's bookmarks.",
        "operationId": "create_bookmark_v1_bookmarks_post",
        "tags": ["User Data"],
        "security": [{"HTTPBearer": []}],
        "requestBody": {
            "required": true,
            "content": { "application/json": { "schema": { "$ref": "#/components/schemas/CreateBookmarkRequest" }}}
        },
        "responses": {
            "201": {
                "description": "Bookmark created successfully.",
                "content": { "application/json": { "schema": { "$ref": "#/components/schemas/Bookmark" }}}
            },
            "401": { "$ref": "#/components/responses/UnauthorizedError" },
            "422": { "$ref": "#/components/responses/ValidationError" }
        }
    }
},
"/v1/bookmarks/{bookmark_id}": {
    "delete": {
        "summary": "Delete Bookmark",
        "description": "Removes an article from the user's bookmarks.",
        "operationId": "delete_bookmark_v1_bookmarks__bookmark_id__delete",
        "tags": ["User Data"],
        "security": [{"HTTPBearer": []}],
        "parameters": [{ "name": "bookmark_id", "in": "path", "required": true, "schema": { "type": "string", "format": "uuid" }}],
        "responses": {
            "204": { "description": "Bookmark deleted successfully." },
            "401": { "$ref": "#/components/responses/UnauthorizedError" },
            "403": { "$ref": "#/components/responses/ForbiddenError" },
            "404": { "$ref": "#/components/responses/NotFoundError" }
        }
    }
},
"/v1/analyses": {
    "get": {
        "summary": "List User Analyses",
        "description": "Retrieves the analysis history for the authenticated user.",
        "operationId": "list_user_analyses_v1_analyses_get",
        "tags": ["User Data"],
        "security": [{"HTTPBearer": []}],
        "responses": {
            "200": {
                "description": "A list of analysis records.",
                "content": { "application/json": { "schema": { "type": "array", "items": { "$ref": "#/components/schemas/AnalysisRecord" }}}}
            },
            "401": { "$ref": "#/components/responses/UnauthorizedError" }
        }
    }
},
"/v1/profile": {
    "get": {
        "summary": "Get User Profile",
        "description": "Retrieves the profile of the authenticated user.",
        "operationId": "get_user_profile_v1_profile_get",
        "tags": ["User Data"],
        "security": [{"HTTPBearer": []}],
        "responses": {
            "200": {
                "description": "User profile data.",
                "content": { "application/json": { "schema": { "$ref": "#/components/schemas/UserProfile" }}}
            },
            "401": { "$ref": "#/components/responses/UnauthorizedError" }
        }
    },
    "patch": {
        "summary": "Update User Profile",
        "description": "Updates the profile of the authenticated user.",
        "operationId": "update_user_profile_v1_profile_patch",
        "tags": ["User Data"],
        "security": [{"HTTPBearer": []}],
        "requestBody": {
            "required": true,
            "content": { "application/json": { "schema": { "$ref": "#/components/schemas/UpdateUserProfileRequest" }}}
        },
        "responses": {
            "200": {
                "description": "Profile updated successfully.",
                "content": { "application/json": { "schema": { "$ref": "#/components/schemas/UserProfile" }}}
            },
            "401": { "$ref": "#/components/responses/UnauthorizedError" },
            "422": { "$ref": "#/components/responses/ValidationError" }
        }
    }
}

// ... inside components.schemas ...

"Bookmark": {
    "type": "object",
    "properties": {
        "id": { "type": "string", "format": "uuid" },
        "user_id": { "type": "string", "format": "uuid" },
        "article_id": { "type": "string", "format": "uuid" },
        "created_at": { "type": "string", "format": "date-time" }
    },
    "required": ["id", "user_id", "article_id", "created_at"]
},
"CreateBookmarkRequest": {
    "type": "object",
    "properties": {
        "article_id": { "type": "string", "format": "uuid", "description": "The ID of the article to bookmark." }
    },
    "required": ["article_id"]
},
"AnalysisRecord": {
    "type": "object",
    "properties": {
        "analysis_id": { "type": "string", "format": "uuid" },
        "article_title": { "type": "string" },
        "article_url": { "type": "string", "format": "uri" },
        "status": { "type": "string", "enum": ["processing", "completed", "failed"] },
        "created_at": { "type": "string", "format": "date-time" }
    },
    "required": ["analysis_id", "article_title", "status", "created_at"]
},
"UserProfile": {
    "type": "object",
    "properties": {
        "id": { "type": "string", "format": "uuid" },
        "username": { "type": "string" },
        "full_name": { "type": "string" },
        "avatar_url": { "type": "string", "format": "uri" },
        "updated_at": { "type": "string", "format": "date-time" }
    },
    "required": ["id", "username"]
},
"UpdateUserProfileRequest": {
    "type": "object",
    "properties": {
        "username": { "type": "string", "description": "A new username." },
        "full_name": { "type": "string", "description": "The user's full name." },
        "avatar_url": { "type": "string", "format": "uri", "description": "URL for a new avatar image."}
    },
    "minProperties": 1
}
```

## 3. Comprehensive Error Documentation

Frontend applications need to handle a range of server responses gracefully. Documenting common error codes for each endpoint is crucial for building resilient UI.

### Suggested Approach

We recommend defining common error responses in the `components.responses` section and referencing them where applicable. This promotes consistency and reusability.

Here are some standard error responses to define:

```json
// ... inside components ...

"responses": {
    "NotFoundError": {
        "description": "The requested resource was not found.",
        "content": { "application/json": { "schema": { "$ref": "#/components/schemas/ErrorModel" }}}
    },
    "UnauthorizedError": {
        "description": "Authentication failed or was not provided.",
        "content": { "application/json": { "schema": { "$ref": "#/components/schemas/ErrorModel" }}}
    },
    "ForbiddenError": {
        "description": "The authenticated user is not permitted to perform this action.",
        "content": { "application/json": { "schema": { "$ref": "#/components/schemas/ErrorModel" }}}
    },
    "ValidationError": {
        "description": "Input validation failed.",
        "content": { "application/json": { "schema": { "$ref": "#/components/schemas/HTTPValidationError" }}}
    }
}

// ... inside components.schemas ...

"ErrorModel": {
    "type": "object",
    "properties": {
        "detail": { "type": "string", "description": "A human-readable description of the error." }
    },
    "required": ["detail"]
}
```

### Example Usage

Here is how you would apply these to an existing endpoint, such as `GET /v1/analysis/{analysis_id}`:

```json
// ... inside paths./v1/analysis/{analysis_id}.get ...
"responses": {
    "200": {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "schema": {
                    "$ref": "#/components/schemas/AnalysisResultsResponse"
                }
            }
        }
    },
    "401": { "$ref": "#/components/responses/UnauthorizedError" },
    "403": { "$ref": "#/components/responses/ForbiddenError" },
    "404": { "$ref": "#/components/responses/NotFoundError" },
    "422": { "$ref": "#/components/responses/ValidationError" }
}
```
This approach makes the API contract clearer and helps the frontend team build more robust error handling logic. 