# OpenAPI v0.4 Refinement Suggestions

First, a huge kudos to the backend team for the progress in `v0.4`! The new unified analysis endpoint (`POST /v1/analyses`) with asynchronous handling is a fantastic improvement and directly addresses our previous feedback.

To build on that great work, here are a few refinement suggestions to further improve consistency and clarity from a consumer's perspective.

---

### User Stories for Backend Improvements

#### 1. Consolidate and Retire Redundant Endpoints
*   **As a** frontend developer,
*   **I want** to use a single set of endpoints for the entire analysis lifecycle (create, poll, retrieve),
*   **so that** the API is self-documenting and I don't have to guess which endpoints are current and which are deprecated.
*   **Suggestion:**
    *   Retire the older analysis endpoints: `POST /v1/analysis/article` and `POST /v1/analysis/article/sync`. The new `POST /v1/analyses` with its `async_mode` flag makes them redundant.
    *   Add a corresponding `GET /v1/analyses/{analysis_id}` endpoint to retrieve the results from a job started by `POST /v1/analyses`. This new GET endpoint should return the same `AnalysisResultsResponse` structure.

#### 2. Standardize API Naming Convention
*   **As a** frontend developer,
*   **I want** all fields in all API responses to follow a single naming convention (e.g., `camelCase`),
*   **so that** the data models are predictable and I can write cleaner, more maintainable code without mapping between `camelCase` and `snake_case`.
*   **Examples of inconsistency:**
    *   `PaginatedAnalysisHistoryResponse` uses `next_cursor` and `total_count`.
    *   `UserProfile` uses `full_name` and `avatar_url`.
    *   `AnalysisHistoryItem` and most newer models use `camelCase` (e.g., `analysisId`).

#### 3. Remove Ambiguous "Legacy" Naming
*   **As a** frontend developer,
*   **I want** API models to have clear names that reflect their current function, without "Legacy" prefixes,
*   **so that** I can confidently use the most current and correct models without ambiguity.
*   **Suggestion:** Rename models like `LegacyAnalysisResultsResponse` and `LegacyFactCheckResult` to something that describes their structure, or better yet, unify them into a single, consistent response model as suggested in the first user story.

#### 4. Unify Fact-Check Result Models
*   **As a** frontend developer,
*   **I want** a single, consistent structure for fact-checking results across the entire API,
*   **so that** I can build a single, reusable component to display fact-check information.
*   **Inconsistency:**
    *   The new `ComprehensiveAnalysisResults` contains `factCheckResults` (an array of `FactCheckResult`).
    *   The older `AnalysisResultTypes` contains `factCheck` (a `LegacyFactCheckResult` object which in turn has a `claims` array).
*   **Suggestion:** Unify on the newer `FactCheckResult` model, which is more detailed and aligns better with the new `ComprehensiveAnalysisResults` structure. 