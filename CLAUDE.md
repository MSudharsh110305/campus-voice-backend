# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

CampusVoice is a FastAPI-based campus complaint management system with AI-powered complaint categorization, intelligent routing, and real-time tracking. Students submit complaints that are automatically categorized and routed to appropriate authorities (Wardens, HODs, Admin Officers, etc.) using LLM-based classification.

## Tech Stack

- **Backend**: FastAPI (async) with Uvicorn
- **Database**: PostgreSQL with SQLAlchemy 2.0 (async ORM)
- **AI/LLM**: Groq API (llama-3.1-8b-instant) with OpenAI fallback
- **Auth**: JWT tokens with passlib/bcrypt
- **Validation**: Pydantic v2 with pydantic-settings
- **Migration**: Alembic
- **Image Processing**: Pillow
- **Testing**: pytest with pytest-asyncio

## Running the Application

### Development Server
```bash
# Run the FastAPI server
python main.py

# Or with uvicorn directly
uvicorn test_main:app --reload --port 8000
```

### Environment Setup
```bash
# Create .env file with required variables
cp .env.example .env  # if available

# Required environment variables:
# - DATABASE_URL (PostgreSQL connection string)
# - JWT_SECRET_KEY (min 32 chars)
# - GROQ_API_KEY (for LLM services)
```

### Database Operations

**Note**: Alembic is not currently set up in this repository. To initialize:

```bash
# Initialize Alembic (if not already done)
alembic init alembic

# Create initial migration
alembic revision --autogenerate -m "initial schema"

# Run migrations
alembic upgrade head

# Create a new migration
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1
```

For development, the database schema is created directly via `SQLAlchemy.create_all()` in the connection module.

### Code Quality & Linting

```bash
# Format code with Black
black src/

# Sort imports with isort
isort src/

# Check style with flake8
flake8 src/

# Type checking with mypy
mypy src/
```

### Testing

**Note**: Test files were recently deleted from this repository. The `test_main.py` file serves as both a test harness and the actual application entry point.

```bash
# Manual/integration testing with the test harness
python test_main.py
# This runs an in-memory FastAPI app with a complete manual test interface

# Automated client testing (requires backend running)
python client_test.py
# Creates 10 students, submits complaints, tests voting, authority actions, etc.

# If pytest tests exist in the future:
pytest
pytest --cov=src --cov-report=html
pytest tests/test_services.py -v
```

## Architecture

### Layer Structure

```
src/
├── api/            # FastAPI routes and dependencies
│   ├── routes/     # Individual route modules (students, complaints, authorities, admin)
│   └── dependencies.py  # Dependency injection (get current user, database session)
├── services/       # Business logic layer
│   ├── llm_service.py          # Groq LLM integration
│   ├── complaint_service.py    # Complaint operations
│   ├── auth_service.py         # Authentication/authorization
│   ├── image_verification.py   # Image validation with LLM
│   └── spam_detection.py       # Spam/abuse detection
├── repositories/   # Data access layer (Repository pattern)
│   ├── base.py              # Base repository with common CRUD
│   ├── complaint_repo.py    # Complaint database operations
│   ├── student_repo.py      # Student database operations
│   └── authority_repo.py    # Authority database operations
├── schemas/        # Pydantic models for validation
│   ├── complaint.py  # ComplaintCreate, ComplaintResponse, etc.
│   ├── student.py    # StudentRegister, StudentLogin, etc.
│   └── common.py     # Shared schemas (pagination, timestamps)
├── database/       # Database configuration
│   ├── models.py      # SQLAlchemy ORM models
│   └── connection.py  # Async engine and session factory
├── middleware/     # FastAPI middleware
│   ├── auth.py         # JWT authentication
│   ├── error_handler.py  # Global exception handling
│   ├── logging.py      # Request/response logging
│   └── rate_limit.py   # Rate limiting (in-memory or Redis)
├── utils/          # Utilities
│   ├── validators.py    # Input validation (email, roll_no, etc.)
│   ├── helpers.py       # Helper functions (time_ago, uuid validation)
│   ├── jwt_utils.py     # JWT encode/decode
│   ├── file_upload.py   # File upload handler
│   └── logger.py        # Application logger setup
└── config/         # Configuration
    ├── settings.py   # Pydantic Settings (loads from .env)
    └── constants.py  # Fixed constants (categories, departments, etc.)
```

### Key Design Patterns

**Repository Pattern**: Data access is abstracted through repository classes. Never write raw SQL in services - use repository methods.

**Service Layer**: Business logic lives in services (`src/services/`), not in routes. Routes should be thin and delegate to services.

**Dependency Injection**: Use FastAPI's `Depends()` for database sessions, current user, etc. See `src/api/dependencies.py`.

**Async Throughout**: All database operations, LLM calls, and I/O are async. Use `await` for all repository/service calls.

## Database Models

### Core Entities

- **Student**: Primary key is `roll_no` (format: `23CS001`). Has department, year, stay_type (Hostel/Day Scholar).
- **Authority**: Hierarchical authorities with `authority_level` (Admin=100, Warden=5, etc.). Can be department-specific (HOD) or global (Admin Officer).
- **Complaint**: UUID primary key. Links to student, category, assigned_authority. Stores original_text and rephrased_text (from LLM).
- **Department**: 13 engineering departments (CSE, ECE, MECH, etc.). Code is unique identifier.
- **ComplaintCategory**: 4 fixed categories (Hostel, General, Department, Disciplinary Committee).

### Important Relationships

- **Complaint → Student**: `student_roll_no` foreign key
- **Complaint → Authority**: `assigned_authority_id` foreign key (who is handling it)
- **Complaint → Department**: `complaint_department_id` for cross-department tracking
- **Image Storage**: Images are stored as binary in `Complaint.image_data` (LargeBinary column), not in filesystem

### Status Workflow

Complaints follow this status flow:
```
Raised → In Progress → Resolved → Closed
   ↓
 Spam (flagged by authority or auto-detected)
```

Valid transitions are defined in `VALID_STATUS_TRANSITIONS` in `constants.py`.

## LLM Integration

### Categorization Flow

1. Student submits complaint text
2. `llm_service.categorize_complaint()` sends text + context to Groq
3. LLM returns category, reasoning, and suggested priority
4. `complaint_service` uses this to assign complaint to authority
5. Authority routing follows `DEFAULT_CATEGORY_ROUTING` rules:
   - Hostel → Warden
   - General → Admin Officer
   - Department → HOD
   - Disciplinary Committee → Disciplinary Committee

### Rephrasing

Complaint text is automatically rephrased to be more formal/professional using `llm_service.rephrase_text()`. Both `original_text` and `rephrased_text` are stored.

### Spam Detection

Two-layer spam detection:
1. **Keyword-based**: Checks against `SPAM_KEYWORDS` in constants
2. **LLM-based**: `llm_service.classify_text()` returns `is_spam`, `is_abusive`, and confidence score

### Image Verification

When images are uploaded to complaints:
1. Image bytes are validated (file type, size)
2. Stored in `Complaint.image_data` as binary (not saved to disk)
3. `image_verification.verify_image()` sends image to LLM vision model
4. Returns `is_relevant`, `is_abusive`, `confidence_score`
5. Status stored in `Complaint.image_verification_status`

## Authentication & Authorization

### JWT Tokens

- Tokens are created in `auth_service.py` using `jwt_utils.py`
- Token payload includes: `{"sub": email, "role": "student"/"authority", "exp": ...}`
- Expiration: 7 days (configurable via `JWT_EXPIRATION_DAYS`)
- Algorithm: HS256 (configurable via `JWT_ALGORITHM`)

### Getting Current User

Routes use `get_current_user` and `get_current_authority` dependencies from `src/api/dependencies.py`. These validate JWT tokens and load user from database.

### Password Hashing

Passwords are hashed with bcrypt using `passlib`. Never store plain passwords. Hash on registration, verify on login.

## Important Constants

Defined in `src/config/constants.py`:

- **CATEGORIES**: List of complaint categories with keywords for LLM hints
- **DEPARTMENTS**: All 13 engineering departments with codes
- **AUTHORITY_LEVELS**: Hierarchy mapping (Admin=100, Warden=5, etc.)
- **DEFAULT_CATEGORY_ROUTING**: Default authority type for each category
- **ESCALATION_RULES**: Auto-escalation paths (Warden → Deputy Warden → Senior Deputy Warden → Admin Officer → Admin)
- **VALID_STATUS_TRANSITIONS**: Allowed status changes
- **SPAM_KEYWORDS**: List of words that trigger spam detection
- **REGEX PATTERNS**: `EMAIL_PATTERN`, `ROLL_NO_PATTERN`, `PASSWORD_PATTERN`

## Settings & Configuration

All settings are in `src/config/settings.py` using Pydantic Settings. Environment variables are loaded from `.env`.

### Critical Settings

- `DATABASE_URL`: Must use `postgresql+asyncpg://` for async support
- `GROQ_API_KEY`: Required for LLM services
- `JWT_SECRET_KEY`: Must be at least 32 characters
- `ENVIRONMENT`: `development`, `staging`, `production`, or `test`

### Feature Flags

- `ENABLE_IMAGE_VERIFICATION`: Enable LLM-based image verification
- `ENABLE_SPAM_DETECTION`: Enable spam detection
- `ENABLE_AUTO_ESCALATION`: Auto-escalate complaints after threshold
- `ENABLE_WEBSOCKET`: Enable WebSocket support

## Visibility Rules

Complaints have three visibility levels:

1. **Private**: Only student and assigned authority can see
2. **Department**: Department members and assigned authority can see
3. **Public**: All students can see, with special rules:
   - Hostel complaints hidden from Day Scholars
   - Department-specific complaints hidden from other departments

Logic is in `complaint_service.get_public_feed()` and implemented in `test_main.py`.

## Vote System

- Students can upvote or downvote public/department complaints
- Each student can vote once per complaint (constraint: `unique_vote_per_student`)
- Vote score = `(upvotes * 5) + (downvotes * -3)`
- Priority auto-adjusts based on vote score:
  - Critical: score >= 200
  - High: score >= 100
  - Medium: score >= 50
  - Low: score < 50

## Common Development Tasks

### Adding a New Route

1. Create route handler in appropriate file in `src/api/routes/`
2. Add business logic in corresponding service in `src/services/`
3. Add data access in repository in `src/repositories/`
4. Define request/response schemas in `src/schemas/`
5. Register route in `src/api/routes/__init__.py`

### Adding a New Database Column

1. Modify model in `src/database/models.py`
2. Create migration: `alembic revision --autogenerate -m "add column"`
3. Review migration file in `alembic/versions/`
4. Apply: `alembic upgrade head`
5. Update schemas in `src/schemas/`
6. Update repository/service logic as needed

### Using LLM Service

Always wrap LLM calls in try/except and provide fallback behavior:

```python
try:
    result = await llm_service.categorize_complaint(text, context)
except Exception as e:
    logger.error(f"LLM categorization failed: {e}")
    # Use fallback: keyword-based categorization
    result = fallback_categorize(text)
```

## Special Notes

### Current Application Entry Point

The application currently imports the FastAPI app from `test_main.py` (see [main.py:21](main.py#L21)). This is an in-memory test harness that provides a complete API implementation without requiring a database. For production or development with a real database, use the app from `src/api/__init__.py`.

### Image Storage Strategy

Images are stored as binary data in PostgreSQL (`LargeBinary` columns), not in the filesystem. This is controlled by `IMAGE_STORAGE_MODE` setting. The current implementation uses database storage with base64 encoding.

### Authority Hierarchy

Authority levels are integers (higher = more power). Admin (level 100) can see all complaints. Lower-level authorities only see complaints assigned to them, unless they're in the escalation chain.

### Async Database Sessions

Always use async context managers for database sessions:

```python
async with get_async_session() as session:
    result = await repository.get_by_id(session, id)
```

Never use synchronous database operations - this will block the event loop.

## Code Style

- Use `async`/`await` for all I/O operations
- Follow FastAPI dependency injection patterns
- Validate inputs with Pydantic schemas
- Log errors with context (`logger.error(f"Context: {e}", exc_info=True)`)
- Use type hints throughout
- Prefer explicit over implicit (clear variable names, no magic numbers)
