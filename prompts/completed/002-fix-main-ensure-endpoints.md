<objective>
Fix main.py to run as a standalone entry point without depending on test_main.py, and ensure all API endpoints work correctly with proper business logic, services, and LLM integration.

Currently, main.py imports the FastAPI app from test_main.py (an in-memory test harness with 1000+ lines of duplicated routes and fake storage). The production-ready app already exists in src/api/__init__.py with proper architecture. main.py must be rewired to use the real app.
</objective>

<context>
Read CLAUDE.md for full project conventions and architecture details.

Key files to examine:
- `main.py` - Current entry point (imports from test_main.py — this is the problem)
- `test_main.py` - In-memory test harness (1000+ lines, duplicates all routes with dict-based storage)
- `src/api/__init__.py` - Production app factory with `create_app()`, lifespan management, exception handlers, middleware
- `src/api/routes/__init__.py` - Route registration (creates api_router and root_router)
- `src/api/routes/students.py` - 12 student endpoints
- `src/api/routes/complaints.py` - 13 complaint endpoints (submit, vote, image upload, spam flagging, etc.)
- `src/api/routes/authorities.py` - 10 authority endpoints (login, dashboard, status update, escalation)
- `src/api/routes/admin.py` - 12 admin endpoints (authority management, analytics, bulk operations)
- `src/api/routes/health.py` - 7 health/monitoring endpoints
- `src/api/dependencies.py` - All dependency injection (auth, DB sessions, pagination, rate limiting, service/repo factories)
- `src/services/` - All 10 service files (complaint_service, llm_service, spam_detection, image_verification, etc.)
- `src/config/settings.py` - Pydantic Settings loaded from .env
- `src/database/connection.py` - Async database engine and session factory
</context>

<requirements>
1. **Rewrite main.py** to import and use the app from `src/api/__init__.py` instead of `test_main.py`:
   - Use the `create_app()` function from `src/api/__init__.py`
   - Keep proper path setup so `src/` is importable
   - Keep uvicorn runner with configurable host/port
   - Ensure the app starts cleanly with `python main.py`
   - The app should initialize the database on startup (the lifespan handler in src/api/__init__.py already does this)

2. **Verify all endpoint business logic is properly wired** — specifically confirm these flows work end-to-end through the route → service → repository chain:

   a. **Complaint Submission Flow**:
      - Student submits complaint text via `POST /api/complaints/submit`
      - Text is processed by LLM service (`llm_service.categorize_complaint()` for category, `llm_service.rephrase_text()` for formal rephrasing)
      - Spam detection runs (`spam_detection.classify_text()`) — if spam, complaint is flagged
      - LLM determines if an image is needed based on complaint content (e.g., infrastructure damage complaints should prompt for image)
      - Complaint is routed to appropriate authority based on category (DEFAULT_CATEGORY_ROUTING in constants.py)
      - Both `original_text` and `rephrased_text` are stored

   b. **Image Upload Flow**:
      - Student uploads image via `POST /api/complaints/{id}/upload-image`
      - Image is stored as binary in `Complaint.image_data`
      - If ENABLE_IMAGE_VERIFICATION is on, `image_verification.verify_image()` checks relevance and abuse
      - `image_verification_status` is updated on the complaint

   c. **Authority Status Change Flow**:
      - Authority views assigned complaints via `GET /api/authorities/my-complaints`
      - Authority updates status via `PUT /api/authorities/complaints/{id}/status`
      - Status must follow valid transitions defined in `VALID_STATUS_TRANSITIONS`
      - Status change creates a history record
      - Notification is sent to the student

   d. **Voting Flow**:
      - Students vote on public/department complaints via `POST /api/complaints/{id}/vote`
      - Vote score recalculated: `(upvotes * 5) + (downvotes * -3)`
      - Priority auto-adjusts based on score thresholds

   e. **Visibility Rules**:
      - Private: only student + assigned authority
      - Department: department members + assigned authority
      - Public: all students, with hostel/department filtering

3. **Fix any broken wiring** — if any route handler calls a service method that doesn't exist, or a service calls a repository method that's missing, fix it. The routes in `src/api/routes/` are well-structured but ensure they connect properly to the services and repositories.

4. **Ensure LLM service fallbacks work** — when GROQ_API_KEY is not set or LLM calls fail, the system should gracefully fall back to keyword-based categorization and skip rephrasing/spam detection rather than crashing.
</requirements>

<implementation>
Follow these steps in order:

1. Read all the files listed in the context section to understand the current state
2. Rewrite `main.py` to use `create_app()` from `src/api/__init__.py`
3. Trace the complaint submission flow from route → service → repository and fix any gaps
4. Trace the authority status update flow and fix any gaps
5. Trace the image upload and verification flow and fix any gaps
6. Verify LLM service has proper try/except with fallback behavior
7. Ensure `src/api/__init__.py` properly registers all routes and middleware
8. Test that `python main.py` starts without import errors (run it briefly to check)

Do NOT:
- Delete test_main.py yet (that's handled in a separate prompt)
- Change API endpoint paths or response schemas (preserve backward compatibility)
- Add new endpoints — only fix existing wiring
- Over-engineer — make minimal changes needed to get everything working correctly
</implementation>

<verification>
Before declaring complete:

1. Run `python main.py` and confirm it starts without errors
2. Check that all route modules are registered (students, complaints, authorities, admin, health)
3. Verify complaint_service.create_complaint() calls LLM for categorization and rephrasing
4. Verify spam_detection is called during complaint submission
5. Verify authority status update follows VALID_STATUS_TRANSITIONS
6. Verify image upload stores binary data and triggers verification when enabled
7. Confirm LLM fallback works (the app shouldn't crash if GROQ_API_KEY is missing)
</verification>

<success_criteria>
- `python main.py` starts the FastAPI server successfully using the production app from src/api/
- All 63+ endpoints are accessible at their correct paths
- Complaint submission processes text through LLM (categorization + rephrasing + spam detection)
- Image upload works with optional LLM verification
- Authority can change complaint status with proper validation
- Voting recalculates priority correctly
- Visibility rules are enforced on public feed
- LLM failures degrade gracefully with fallbacks, not crashes
</success_criteria>
