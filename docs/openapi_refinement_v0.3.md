# OpenAPI v0.3 Refinement Suggestions

Here is a summary of feedback on the `backend_openapi_v0.3.json` specification from a frontend development and user experience perspective.

---

### User Stories for Backend Improvements

#### 1. Unified Analysis Endpoint
*   **As a** frontend developer,
*   **I want** a single, unified endpoint to submit an article for any type of analysis,
*   **so that** I don't have to build and maintain separate logic for the "comprehensive" and "legacy" analysis flows.

#### 2. Consistent Analysis Response Model
*   **As a** frontend developer,
*   **I want** all analysis endpoints (sync and async) to return the same, consistent JSON structure for the results,
*   **so that** I can simplify frontend state management and create reusable components without needing complex data transformation logic.

#### 3. Asynchronous by Default for Heavy Operations
*   **As a** user,
*   **I want** all potentially long-running operations, like the "comprehensive" analysis, to be handled asynchronously,
*   **so that** the application remains responsive and I'm not stuck on a loading screen that might time out. The API should immediately return a task ID that the frontend can use to poll for the result.

#### 4. Consistent API Naming Conventions
*   **As a** frontend developer,
*   **I want** all properties in API responses to follow a single, consistent naming convention (e.g., `camelCase`),
*   **so that** the code is cleaner, more predictable, and I don't have to mentally switch between `analysisId` and `next_cursor`.

#### 5. Clear and Unambiguous Naming
*   **As a** frontend developer,
*   **I want** API models to have clear, descriptive names without confusing prefixes like "Legacy",
*   **so that** I can be confident about their intended use and longevity without having to ask for clarification. 