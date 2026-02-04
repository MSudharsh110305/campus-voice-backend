<objective>
Perform a complete rewrite of the CampusVoice backend, going through the entire project and database to implement proper logic, create/modify endpoints, and ensure all operations work correctly. The current implementation may have ambiguous or incomplete logic - you need to analyze, redesign, and rewrite components to meet the full requirements.

This is critical for creating a production-ready AI-powered complaint management system where students submit complaints with optional images (as determined by LLM), the system enforces intelligent image requirements, implements partial anonymity, and properly handles spam detection with clear user feedback.
</objective>

<context>
CampusVoice is a FastAPI-based complaint management system with:
- **Student features**: Register, login, submit complaints (text + optional images), view my complaints, track status, view public feed with filters, vote on public complaints
- **Authority features**: Login, view assigned complaints, change status, post updates to public feed
- **Admin features**: Full permissions - view all complaints, change any status, access student information
- **LLM Integration (Groq API)**: Rephrase complaints, categorize, assign authorities, set initial priority, spam/abuse detection, image-text relevance verification, **determine if image is required**
- **Voting System**: Real-time voting that dynamically adjusts priority scores
- **Visibility Rules**: Department-specific filtering, hostel/day scholar separation in public feed
- **Partial Anonymity**: Admin can view all student information; authorities can only see student information if complaint is marked as spam
- **Database**: PostgreSQL (password: 110305). You may delete and recreate the database if schema/structure changes are needed.

**Important**: The current implementation may have ambiguous logic. You have full authority to create proper endpoint logic, redesign flows, and rewrite components as needed to meet requirements correctly.

Read [CLAUDE.md](CLAUDE.md) for initial architecture reference, but feel free to redesign as needed.

Key files to examine and rewrite:
@src/api/routes/
@src/services/
@src/repositories/
@src/database/models.py
@src/config/settings.py
@src/config/constants.py
@main.py
@test_main.py
</context>

<requirements>
Implement the following critical requirements:

**1. LLM-Driven Image Requirements**
- When a student submits complaint text, send it to the LLM to analyze if images are **compulsory** for that complaint
- If LLM determines image is required:
  - Endpoint must enforce image upload (reject submission without image)
  - Support single or multiple images as needed
  - Provide clear error message: "This complaint requires supporting images. Please upload at least one image."
- If LLM determines image is optional:
  - Allow submission with or without images
- The LLM should consider complaint type, severity, and nature when determining image necessity

**2. Partial Anonymity System**
- **Admin role**: Can view all student information (name, email, roll number, department, etc.) for all complaints
- **Authority role**: Can view student information ONLY if the complaint is marked as spam
  - For non-spam complaints: Show only complaint content, status, category - hide student personal details
  - For spam complaints: Reveal student information to help authorities identify repeat offenders
- Create/modify endpoints to implement this logic:
  - `/api/authorities/my-complaints` - filter student info based on spam status
  - `/api/complaints/{id}` - conditionally include student details based on requester role and spam status

**3. Spam/Abusive Content Handling**
- When complaint text or image is detected as spam/abusive by LLM:
  - Endpoint should respond with clear indication (HTTP 400 or 422)
  - Response body: `{"success": false, "error": "Complaint marked as spam/abusive", "reason": "...", "is_spam": true}`
  - Do NOT create the complaint in database with "Spam" status - reject it outright
  - Log the spam attempt for monitoring
- Provide specific feedback on why it was marked as spam (if LLM provides reasoning)

**4. Complete Rewrite Authorization**
- Go through the **entire project and database**
- Current implementation may be ambiguous - create proper logic for all endpoints
- Feel free to:
  - Redesign database schemas if needed (delete and recreate PostgreSQL database)
  - Restructure endpoint logic and flows
  - Rewrite services, repositories, and routes
  - Add missing endpoints or remove unnecessary ones
  - Improve error handling, validation, and user feedback

**5. Core Functionality (must work end-to-end)**
- Student: Register, login, submit complaints (with LLM-driven image requirement), view my complaints, view public feed with filters, vote on complaints
- Authority: Login, view assigned complaints (with partial anonymity), change status, post updates
- Admin: Full access to all complaints and student information
- LLM Integration: Rephrase, categorize, assign authority, check spam, verify images, **determine image necessity**
- Voting: Real-time priority updates
- Visibility: Department and stay_type filtering

**6. Database Management**
- PostgreSQL password: `110305`
- You may delete existing database and recreate with new schemas if needed
- Ensure proper migrations or initialization scripts
- Seed necessary data (authorities, departments, categories)

**7. Host Readiness**
- Application must start with `python main.py` without errors
- All dependencies properly configured
- Environment variables validated
- Ready for local testing of all operations
</requirements>

<implementation>
Follow this systematic approach for complete rewrite:

**Phase 1: Deep Analysis & Planning**
Thoroughly analyze the entire project to understand:
- Current implementation and its limitations
- Database schema and relationships
- LLM integration points and flows
- Authentication and authorization patterns
- Missing features and ambiguous logic
- Endpoint structure and API design

Create a redesign plan documenting:
- Database schema changes needed (if any)
- New/modified endpoints required
- LLM service enhancements (image necessity detection)
- Partial anonymity implementation approach
- Spam rejection flow

**Phase 2: Database Redesign (if needed)**
If schema changes are required:
1. Document current schema issues
2. Design new schema with proper relationships
3. Delete existing PostgreSQL database (password: 110305)
4. Create new database with updated models
5. Write initialization/migration scripts
6. Seed required data (departments, categories, authorities)

**Phase 3: Core Service Rewrite**
Rewrite services with proper logic:

**LLM Service (`src/services/llm_service.py`)**:
- Add `check_image_required(complaint_text: str) -> bool` method
- LLM should analyze complaint and return whether image is compulsory
- Consider complaint type, severity, and nature (e.g., infrastructure issues likely need images)
- Enhance spam detection to provide specific reasoning
- Improve error handling and fallback logic

**Complaint Service (`src/services/complaint_service.py`)**:
- Implement LLM-driven image requirement check before accepting complaint
- Enforce image upload if LLM determines it's required
- Reject spam/abusive complaints outright (don't create in DB)
- Implement partial anonymity filtering for authority access
- Handle multi-image uploads

**Auth Service (`src/services/auth_service.py`)**:
- Ensure proper role-based access control (Student, Authority, Admin)
- Implement permission checks for partial anonymity

**Phase 4: Endpoint Rewrite**
Rewrite all endpoints with proper logic:

**Student Endpoints (`src/api/routes/students.py`)**:
- `POST /api/students/complaints` - Check image requirement via LLM first
  - If image required but not provided: HTTP 400 with clear message
  - If spam detected: HTTP 400 with spam indication
  - Support multiple image uploads
- `GET /api/students/my-complaints` - Full complaint details for own complaints
- `GET /api/complaints/public-feed` - Proper visibility filtering

**Authority Endpoints (`src/api/routes/authorities.py`)**:
- `GET /api/authorities/my-complaints` - Implement partial anonymity
  - Non-spam complaints: Hide student personal info
  - Spam complaints: Show full student details
- `GET /api/complaints/{id}` - Conditional student info based on spam status

**Admin Endpoints (`src/api/routes/admin.py`)**:
- Full access to all complaints with complete student information
- No anonymity restrictions

**Phase 5: Schema & Model Updates**
Update Pydantic schemas:
- Add `image_required` field to complaint response
- Add `is_spam_rejected` field for spam responses
- Create conditional response schemas for partial anonymity
- Support multiple images in complaint schemas

**Phase 6: Testing & Validation**
- Test all endpoints end-to-end
- Verify LLM image requirement logic
- Validate partial anonymity enforcement
- Test spam rejection flow
- Ensure database operations work correctly
- Verify host readiness

**What to maintain:**
- FastAPI framework and async patterns
- Repository pattern for data access
- Service layer for business logic
- Pydantic validation
- JWT authentication foundation
- General code structure (routes/services/repositories separation)

**What to rewrite/redesign:**
- LLM integration to add image necessity detection
- Complaint submission flow with image requirement enforcement
- Spam handling (reject instead of marking)
- Authority complaint viewing with partial anonymity
- Endpoint response structures
- Database schema (if needed)
- Error messages and user feedback
- Any ambiguous or incomplete logic
</implementation>

<analysis_approach>
For maximum efficiency, perform parallel analysis when examining independent modules:
- Read multiple route files simultaneously
- Examine related service and repository files together
- Cross-reference schemas with models in parallel

After receiving analysis results, carefully reflect on:
- Patterns that repeat across modules (good or bad)
- Critical dependencies between components
- Potential cascading issues from fixes
</analysis_approach>

<output>
1. **Implementation Report**: Create `./implementation-report.md` documenting:
   - Design decisions and approach for new features
   - Database schema changes (if any were made)
   - How LLM image requirement check was implemented
   - How partial anonymity was implemented
   - How spam rejection flow was implemented
   - Key logic decisions and rationale
   - Any breaking changes or migration notes

2. **Rewritten Code**: Complete rewrite of necessary files:
   - **Services** (`src/services/`):
     - Enhanced `llm_service.py` with image requirement detection
     - Rewritten `complaint_service.py` with new flows
     - Updated other services as needed
   - **Routes** (`src/api/routes/`):
     - Rewritten complaint submission endpoints
     - Modified authority endpoints for partial anonymity
     - Enhanced admin endpoints
   - **Repositories** (`src/repositories/`):
     - Updated query logic for partial anonymity
     - Enhanced complaint repository methods
   - **Schemas** (`src/schemas/`):
     - New response schemas for partial anonymity
     - Updated complaint schemas for multi-image support
     - Spam rejection response schemas
   - **Models** (`src/database/models.py`):
     - Schema changes if needed
   - **Configuration** (`src/config/`):
     - Updated settings and constants as needed

3. **Database Setup**:
   - SQL scripts or Python scripts for database initialization (if recreated)
   - Seed data scripts for authorities, departments, categories
   - Migration notes (if applicable)

4. **Testing Guide**: Add to implementation report:
   - How to test LLM image requirement feature
   - How to verify partial anonymity
   - How to test spam rejection
   - Sample API calls for testing all flows
   - Confirmation that all endpoints are operational
</output>

<verification>
Before declaring complete, verify:

**Critical New Features**:
- [ ] LLM image requirement check works correctly
  - [ ] LLM analyzes complaint text and determines if image is compulsory
  - [ ] Endpoint enforces image upload when LLM requires it
  - [ ] Clear error message when required image is missing
  - [ ] Complaint submission succeeds when image requirement is met
- [ ] Spam/abusive content is rejected outright
  - [ ] Endpoint returns HTTP 400/422 for spam complaints
  - [ ] Response clearly indicates spam detection with reason
  - [ ] Spam complaints are NOT created in database
  - [ ] Spam attempts are logged for monitoring
- [ ] Partial anonymity is enforced
  - [ ] Admin can see all student information for all complaints
  - [ ] Authorities can see student info ONLY for spam complaints
  - [ ] Non-spam complaints hide student details from authorities
  - [ ] Endpoint responses conditionally include student data

**Endpoint Testing**:
- [ ] Student registration and login work
- [ ] Complaint submission with LLM image check works
  - [ ] Test complaint requiring image (rejected without image)
  - [ ] Test complaint not requiring image (accepted without image)
  - [ ] Test multiple image uploads
  - [ ] Test spam complaint (rejected with clear message)
- [ ] My complaints endpoint returns correct data
- [ ] Public feed respects visibility and filtering rules
- [ ] Voting updates priority in real-time
- [ ] Authority login and complaint viewing work with partial anonymity
  - [ ] Non-spam complaints hide student details
  - [ ] Spam complaints show student details
- [ ] Status updates by authorities work
- [ ] Authority updates post to public feed
- [ ] Admin has full access permissions with complete student info

**Code Quality**:
- [ ] No import errors or missing dependencies
- [ ] All async functions use await correctly
- [ ] Repository pattern consistently applied
- [ ] Service layer handles business logic (not routes)
- [ ] Proper error handling in all services
- [ ] LLM calls have fallback behavior
- [ ] Database sessions use async context managers
- [ ] Clear, informative error messages for users

**Host Readiness**:
- [ ] Environment variables validated in settings
- [ ] Database connection initializes correctly (PostgreSQL password: 110305)
- [ ] Database schema is correct (recreated if needed)
- [ ] Required data is seeded (authorities, departments, categories)
- [ ] FastAPI app starts with `python main.py` without errors
- [ ] Middleware stack is complete
- [ ] CORS configured for frontend
- [ ] Logging configured properly
- [ ] All required dependencies in requirements.txt

**Logic Correctness**:
- [ ] LLM image necessity logic is sound and provides useful results
- [ ] Authority assignment follows proper routing logic
- [ ] Visibility rules correctly filter complaints
- [ ] Vote score calculation matches formula: (upvotes * 5) + (downvotes * -3)
- [ ] Priority thresholds correctly applied
- [ ] Status transitions follow valid paths
- [ ] Spam detection works for both text and images
- [ ] Image verification integrates with LLM correctly
- [ ] Partial anonymity logic is consistently applied across all endpoints
</verification>

<success_criteria>
1. **LLM-Driven Image Requirements**: Complaint submission checks with LLM if image is required, enforces upload if necessary, provides clear user feedback
2. **Spam Rejection**: Spam/abusive complaints are rejected outright (not stored), with clear error responses indicating spam detection
3. **Partial Anonymity**: Admin sees all student info; authorities see student info only for spam complaints; non-spam complaints hide student details from authorities
4. **Complete Rewrite**: Entire project has been analyzed and rewritten with proper logic, no ambiguous implementations remain
5. **Database Ready**: PostgreSQL database is properly configured (password: 110305), schema is correct (recreated if needed), required data is seeded
6. **All Endpoints Work**: Student, authority, and admin flows are fully operational and testable end-to-end
7. **Host Ready**: Application starts with `python main.py` without errors, all dependencies configured, ready for local testing
8. **Code Quality**: Consistent patterns, proper error handling, clear user feedback, maintainable structure
9. **Documentation**: Analysis report documents design decisions, schema changes (if any), and implementation approach
</success_criteria>
