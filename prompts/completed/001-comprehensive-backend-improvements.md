<objective>
Comprehensively improve the CampusVoice backend to be production-ready with enhanced LLM-powered features, real-time WebSocket updates, and fixed voting system. This task involves thoroughly analyzing the entire codebase and implementing critical improvements without breaking existing functionality.

The end goal is a fully functional, deployment-ready backend that:
1. Uses improved LLM for spam/abuse detection and image requirement analysis
2. Validates complaint text-image relevance using LLM
3. Supports real-time voting on public complaints via WebSocket
4. Enables real-time status updates for authorities via WebSocket
5. Handles all operations on all endpoints without errors
</objective>

<context>
This is a FastAPI-based campus complaint management system with:
- **Tech Stack**: FastAPI (async), PostgreSQL, SQLAlchemy 2.0 (async), Groq LLM, JWT auth
- **Current State**: Basic LLM integration exists, voting system has issues, no WebSocket support
- **Key Files to Review**:
  - @CLAUDE.md - Project overview and architecture
  - @src/services/llm_service.py - Current LLM integration
  - @src/services/complaint_service.py - Complaint business logic
  - @src/services/spam_detection.py - Spam detection logic
  - @src/services/image_verification.py - Image verification logic
  - @src/api/routes/complaints.py - Complaint endpoints
  - @src/database/models.py - Database models
  - @src/config/settings.py - Configuration and feature flags

**CRITICAL**: The backend must remain fully functional. Do not break existing logic or endpoints.
</context>

<requirements>

## 1. Enhanced LLM Spam/Abuse Detection

**Text Analysis:**
- Improve `llm_service.py` to provide more accurate spam and abuse detection
- Use contextual analysis (complaint category, student history, text patterns)
- Return confidence scores and reasoning for decisions
- Handle edge cases (sarcasm, cultural context, genuine grievances that sound harsh)

**Image Analysis:**
- Enhance `image_verification.py` to detect abusive/inappropriate images
- Check if images are relevant to complaint context
- Return detailed analysis: `is_relevant`, `is_abusive`, `confidence_score`, `reasoning`

## 2. LLM-Powered Image Requirement Analysis

**New Feature:**
- Before accepting complaint submission, use LLM to analyze if the complaint text requires photographic evidence
- Examples requiring images: "AC not working", "water leakage", "broken equipment", "damaged property"
- Examples NOT requiring images: "policy change request", "schedule conflict", "general suggestions"
- If image is required but not provided, return 400 error with clear message
- If image is provided but not required, accept it anyway (optional evidence is fine)

**Implementation:**
- Add new method in `llm_service.py`: `async def requires_image_evidence(complaint_text: str, category: str) -> dict`
- Return: `{"requires_image": bool, "reasoning": str, "confidence": float}`
- Integrate into complaint submission flow in `complaint_service.py`

## 3. Complaint Text-Image Relevance Validation

**Logic:**
- When both text and image are provided, use LLM to verify they are related
- Example: Text about "hostel mess food" with image of classroom → SPAM
- Example: Text about "broken AC" with image of AC unit → VALID
- If unrelated, mark complaint as spam and reject with 400 error
- Store validation results in database for audit trail

**Implementation:**
- Add method: `async def validate_text_image_relevance(text: str, image_data: bytes, category: str) -> dict`
- Return: `{"is_relevant": bool, "reason": str, "confidence": float}`
- Integrate into complaint submission validation flow

## 4. Real-Time Voting System (WebSocket)

**Current Issues to Fix:**
- Review existing voting logic in `complaint_service.py` and models
- Ensure vote constraints work (one vote per student per complaint)
- Fix priority calculation based on votes: `score = (upvotes * 5) + (downvotes * -3)`
- Priority mapping: Critical (≥200), High (≥100), Medium (≥50), Low (<50)

**WebSocket Integration:**
- Implement WebSocket endpoint: `/ws/complaints/{complaint_id}`
- When student votes, broadcast updated vote counts and priority to all connected clients
- Message format: `{"type": "vote_update", "complaint_id": "...", "upvotes": X, "downvotes": Y, "priority": "High"}`
- Handle connection lifecycle (connect, disconnect, reconnect)

**Files to Create/Modify:**
- Create `src/api/routes/websocket.py` for WebSocket routes
- Add WebSocket manager in `src/utils/websocket_manager.py`
- Modify voting endpoints to trigger WebSocket broadcasts

## 5. Real-Time Authority Status Updates (WebSocket)

**Feature:**
- When authority changes complaint status (Raised → In Progress → Resolved → Closed)
- Broadcast status change to all connected clients (students and authorities)
- Students see their complaints update in real-time
- Authorities see their assigned complaints update in real-time

**WebSocket Endpoint:**
- `/ws/complaints` - General complaint updates channel
- Broadcast message format: `{"type": "status_update", "complaint_id": "...", "status": "In Progress", "updated_by": "Warden", "timestamp": "..."}`

**Implementation:**
- Modify `authority_status_change` logic in routes/authorities.py
- Trigger WebSocket broadcast after successful status update
- Ensure proper authorization (only show updates user is allowed to see)

## 6. Code Quality & Deployment Readiness

**Testing:**
- After all changes, test with @test-api-comprehensive.py
- All 12 tests MUST pass
- Fix any errors that arise from your changes
- Ensure no regression in existing functionality

**Error Handling:**
- Add proper error handling for all LLM calls (handle timeouts, API failures)
- Provide fallback behavior when LLM is unavailable
- Log errors comprehensively for debugging

**Configuration:**
- Check `ENABLE_WEBSOCKET`, `ENABLE_IMAGE_VERIFICATION`, `ENABLE_SPAM_DETECTION` flags in settings.py
- Ensure features can be toggled via environment variables
- Add any new configuration options needed

</requirements>

<implementation>

## Step-by-Step Approach

### Phase 1: Analysis & Planning (Use Explore agent for thoroughness)
1. Thoroughly analyze the entire codebase to understand current implementation
2. Identify all files that need modification
3. Document current LLM integration patterns
4. Review existing voting system and identify bugs
5. Check if WebSocket dependencies exist in requirements.txt

### Phase 2: LLM Service Enhancements
1. Improve `llm_service.py` with better prompts and error handling
2. Add `requires_image_evidence()` method with comprehensive LLM prompt
3. Add `validate_text_image_relevance()` method for image-text correlation
4. Enhance `classify_text()` for better spam detection with context awareness
5. Update `image_verification.py` to integrate with new LLM methods

### Phase 3: WebSocket Infrastructure
1. Add WebSocket dependencies to requirements.txt if missing (websockets, python-socketio, etc.)
2. Create WebSocket manager class (`src/utils/websocket_manager.py`)
   - Handle connection pool
   - Broadcast to specific channels/rooms
   - Handle authentication via JWT
3. Create WebSocket routes (`src/api/routes/websocket.py`)
4. Register WebSocket routes in main app

### Phase 4: Voting System Fixes
1. Review and fix vote calculation logic
2. Ensure database constraints are correct (unique vote per student per complaint)
3. Add transaction handling to prevent race conditions
4. Integrate WebSocket broadcasts into voting endpoints
5. Test vote counting and priority updates

### Phase 5: Status Update Real-Time Features
1. Modify authority status change endpoints
2. Add WebSocket broadcast after status updates
3. Ensure proper authorization (don't broadcast private complaints publicly)
4. Add audit logging for status changes

### Phase 6: Integration & Testing
1. Integrate image requirement check into complaint submission flow
2. Add text-image relevance validation
3. Test all endpoints with test suite
4. Fix any issues that arise
5. Verify WebSocket connections work properly
6. Test real-time updates from multiple clients

### Phase 7: Final Verification
1. Run @test-api-comprehensive.py - ensure all 12 tests pass
2. Test WebSocket connections manually if needed
3. Review logs for any errors or warnings
4. Confirm all feature flags work correctly
5. Document any new environment variables or setup steps

## Important Constraints

**DO NOT:**
- Break existing API endpoints or change response formats
- Remove or modify existing database columns without migration
- Change authentication/authorization logic unless fixing bugs
- Disable existing features
- Use synchronous database operations (always use async/await)

**DO:**
- Follow existing code patterns and architecture (Repository → Service → Route)
- Use dependency injection for database sessions and current user
- Add comprehensive error handling and logging
- Write clear, descriptive commit messages
- Test thoroughly before declaring complete

**WHY these constraints matter:**
- The backend is already partially functional and in use
- Breaking changes would require frontend modifications
- Async operations are critical for performance with WebSocket connections
- Following patterns ensures maintainability and consistency

## Handling Ambiguity

If you encounter unclear requirements or multiple valid approaches:
1. Analyze the trade-offs of each approach
2. Choose the approach that best fits existing architecture
3. Document your decision and reasoning
4. If truly uncertain, ask the user for clarification using AskUserQuestion

**Recommended approaches for common decisions:**
- **WebSocket library**: Use `fastapi.WebSocket` (built-in) for simplicity, or python-socketio for advanced features
- **LLM prompts**: Be specific and provide examples in prompts for better accuracy
- **Error handling**: Log errors but don't expose internal details to API responses
- **Broadcasting**: Use room-based broadcasting (per complaint) to reduce unnecessary messages

</implementation>

<output>

Files to create:
- `./src/utils/websocket_manager.py` - WebSocket connection manager
- `./src/api/routes/websocket.py` - WebSocket route handlers

Files to modify:
- `./src/services/llm_service.py` - Add image requirement and relevance validation methods
- `./src/services/complaint_service.py` - Integrate LLM checks and WebSocket broadcasts
- `./src/services/spam_detection.py` - Enhance with improved LLM logic
- `./src/services/image_verification.py` - Add relevance checking
- `./src/api/routes/complaints.py` - Add image requirement validation
- `./src/api/routes/authorities.py` - Add WebSocket broadcast on status change
- `./src/database/models.py` - Add any missing fields (image_required, relevance_score, etc.)
- `./src/config/settings.py` - Add WebSocket configuration
- `./requirements.txt` - Add WebSocket dependencies if needed

</output>

<verification>

Before declaring complete, verify:

1. **LLM Features Work:**
   - Test image requirement detection with various complaint texts
   - Test text-image relevance validation with related and unrelated pairs
   - Verify spam detection catches obvious spam but allows genuine complaints

2. **Voting System Works:**
   - Students can vote (upvote/downvote) on public complaints
   - Each student can only vote once per complaint
   - Vote counts update correctly in database
   - Priority updates based on vote score
   - WebSocket broadcasts vote updates to connected clients

3. **Real-Time Updates Work:**
   - WebSocket connections establish successfully
   - Status changes broadcast to connected clients
   - Vote updates broadcast to connected clients
   - Clients receive only updates they're authorized to see

4. **All Tests Pass:**
   - Run: `python test-api-comprehensive.py`
   - All 12 tests must pass
   - No regression in existing functionality

5. **Error Handling:**
   - LLM failures don't crash the application
   - Proper error messages returned to clients
   - Logs contain useful debugging information

6. **Configuration:**
   - All feature flags work correctly
   - WebSocket can be enabled/disabled via config
   - Environment variables are documented

</verification>

<success_criteria>

The task is complete when:

1. ✅ LLM accurately determines when images are required for complaints
2. ✅ LLM validates text-image relevance and rejects mismatched submissions
3. ✅ Enhanced spam/abuse detection catches problematic content with better accuracy
4. ✅ Voting system works correctly with real-time WebSocket updates
5. ✅ Authority status changes broadcast in real-time via WebSocket
6. ✅ All 12 tests in test-api-comprehensive.py pass without errors
7. ✅ No existing functionality is broken
8. ✅ Backend is deployment-ready (proper error handling, logging, configuration)
9. ✅ Code follows existing patterns and architecture

**Final checkpoint:** Run the comprehensive test suite and manually test WebSocket connections. If everything works, create a detailed commit with all changes.

</success_criteria>

<parallel_tool_calling>
For maximum efficiency, whenever you need to perform multiple independent operations (like reading multiple unrelated files, running multiple independent commands, or searching different parts of the codebase), invoke all relevant tools simultaneously rather than sequentially. This significantly speeds up the agentic workflow.
</parallel_tool_calling>

<reflection_after_tools>
After receiving tool results (especially from complex operations like Explore agent, multiple file reads, or test runs), carefully reflect on:
- What the results tell you about the current state
- What approach to take next
- Whether you need additional information before proceeding
- Potential issues or edge cases to consider

Take time to think through the implications before making changes.
</reflection_after_tools>
