<objective>
Delete all old test files from the project root and create a new comprehensive API test script (`test-api-comprehensive.py`) that exercises the full CampusVoice API end-to-end. The script should print actual API responses for each operation rather than pass/fail assertions.

This test script is meant to serve as both a verification tool and a demo of the entire system working — someone reading the output should understand exactly what each API call returns.
</objective>

<context>
Read CLAUDE.md for full project conventions and architecture details.

Key files to examine before writing the test script:
- `src/api/routes/students.py` - Student endpoints (register, login, profile, my-complaints, notifications)
- `src/api/routes/complaints.py` - Complaint endpoints (submit, vote, image upload, public feed, status history)
- `src/api/routes/authorities.py` - Authority endpoints (login, dashboard, my-complaints, status update, escalate)
- `src/api/routes/admin.py` - Admin endpoints (authority management, analytics, bulk operations)
- `src/api/routes/health.py` - Health check endpoints
- `src/schemas/complaint.py` - Complaint request/response schemas
- `src/schemas/student.py` - Student request/response schemas
- `src/config/constants.py` - Categories, departments, valid status transitions, authority levels
- `src/database/models.py` - Database models (for understanding field names and relationships)
- `main.py` - Entry point (the test script will hit the running server via HTTP requests)
</context>

<requirements>
1. **Delete old test files** from the project root:
   - `test_main.py`
   - `client.py`
   - `client_test.py`
   - `test_repositories.py`
   - `test_schemas.py`
   - `test_services_comprehensive.py`
   - `test_system.py`
   - `test_utils.py`
   - `__pycache__/test_main.cpython-313.pyc` (if it exists)

   Only delete files that actually exist. Do not delete any files inside `src/`.

2. **Create `test-api-comprehensive.py`** at the project root with the following characteristics:

   **General Design**:
   - Uses `requests` library (synchronous HTTP client) to hit the running server at `http://localhost:8000`
   - Each operation prints a clear header (e.g., `=== REGISTERING STUDENT 1 ===`) followed by the full JSON response
   - Uses `json.dumps(response.json(), indent=2)` for pretty-printed responses
   - Prints HTTP status code alongside each response
   - Runs sequentially — each section builds on the previous (tokens from login used in subsequent calls)
   - Includes a brief pause between operations if needed for async processing
   - Wraps everything in a `main()` function with `if __name__ == "__main__"` guard
   - Includes error handling so one failure doesn't stop the entire script — print the error and continue

   **Test Scenarios (in this order)**:

   a. **Health Check**:
      - `GET /health` — print server status
      - `GET /health/detailed` — print detailed health

   b. **Student Registration** (create 3-4 students with different profiles):
      - Student 1: CSE department, Hostel, Year 2 (e.g., roll_no: 23CS001)
      - Student 2: ECE department, Day Scholar, Year 3 (e.g., roll_no: 22EC045)
      - Student 3: MECH department, Hostel, Year 1 (e.g., roll_no: 24ME012)
      - Student 4: CSE department, Hostel, Year 2 (e.g., roll_no: 23CS050) — same department as Student 1
      - Print full registration response for each

   c. **Student Login** (login all students, store tokens):
      - Login each student, print response, extract JWT token
      - Also test invalid login (wrong password) — print the error response

   d. **Get Student Profile**:
      - `GET /api/students/profile` for Student 1 — print profile

   e. **Submit Complaints** (various scenarios):
      - Complaint 1 (Student 1): Hostel complaint — "The water supply in Hostel Block A has been irregular for the past week. The taps run dry every evening between 6-9 PM." (visibility: public)
      - Complaint 2 (Student 2): Department complaint — "The projector in ECE seminar hall Room 201 has been broken for two weeks. Faculty are unable to conduct presentations." (visibility: department)
      - Complaint 3 (Student 3): General complaint — "The campus WiFi in the library building is extremely slow during peak hours. Students cannot access online resources for assignments." (visibility: public)
      - Complaint 4 (Student 1): Complaint that should require an image — "There is a large crack in the wall of Room 105 in Hostel Block B. It appeared after the recent heavy rains and looks like a structural issue." (visibility: public)
      - Complaint 5 (Student 4): Spam/abusive complaint — Use clearly inappropriate/spammy text to test spam detection (e.g., "This is stupid garbage, everything sucks, you idiots don't do anything, I hate this useless college") (visibility: public)
      - Complaint 6 (Student 3): Private complaint — "I am facing issues with my hostel roommate. There have been multiple incidents of my belongings going missing." (visibility: private)
      - Print full response for each, noting the LLM categorization, assigned authority, and spam detection results

   f. **Image Upload** (for the complaint that requires an image):
      - Create a small test image programmatically (use Pillow to generate a simple 100x100 colored image)
      - Upload to Complaint 4 via `POST /api/complaints/{id}/upload-image`
      - Print response including verification status

   g. **Public Feed**:
      - `GET /api/complaints/public-feed` as Student 1 (Hostel, CSE) — print feed
      - `GET /api/complaints/public-feed` as Student 2 (Day Scholar, ECE) — print feed (should NOT see hostel complaints)
      - Note visibility differences in output

   h. **Voting**:
      - Student 2 upvotes Complaint 1 (hostel complaint) — print response
      - Student 3 upvotes Complaint 1 — print response
      - Student 4 upvotes Complaint 1 — print response
      - Student 1 upvotes Complaint 3 (WiFi complaint) — print response
      - Student 2 downvotes Complaint 3 — print response
      - Check vote on Complaint 1: `GET /api/complaints/{id}/my-vote` as Student 2 — print response
      - Remove vote: `DELETE /api/complaints/{id}/vote` as Student 2 — print response
      - Re-check public feed to see updated vote counts — print response

   i. **Authority Login & Dashboard**:
      - Login as an authority (use one that was auto-created or create via admin) — print response
      - `GET /api/authorities/dashboard` — print dashboard with stats
      - `GET /api/authorities/my-complaints` — print assigned complaints (note partial anonymity — student info should be hidden for non-spam)

   j. **Authority Status Changes**:
      - Change Complaint 1 status to "In Progress" — print response
      - Post an update on Complaint 1: "We are looking into the water supply issue. A plumber has been contacted." — print response
      - Change Complaint 1 status to "Resolved" — print response
      - Print the status history for Complaint 1: `GET /api/complaints/{id}/status-history`
      - Print the full timeline for Complaint 1: `GET /api/complaints/{id}/timeline`

   k. **Student Notifications**:
      - `GET /api/students/notifications` as Student 1 — should have notifications about status changes
      - `GET /api/students/notifications/unread-count` — print count
      - Mark one as read — print response

   l. **My Complaints**:
      - `GET /api/students/my-complaints` as Student 1 — print all their complaints with current statuses

   m. **Complaint Details**:
      - `GET /api/complaints/{id}` for Complaint 1 — print full details including vote counts, status, authority info

   **Output Format for Each Operation**:
   ```
   ============================================================
   === OPERATION NAME ===
   ------------------------------------------------------------
   Endpoint: METHOD /path

   [Status Code: 200]
   Response:
   {
     "field": "value",
     ...
   }
   ============================================================
   ```

3. **Script should be runnable with**: `python test-api-comprehensive.py`
   - Requires the server to be running on localhost:8000
   - Print a clear message at the start: "Make sure the CampusVoice server is running on http://localhost:8000"
   - Accept optional `--base-url` argument to override the server URL
   - At the end, print a summary of all operations performed and their status codes
</requirements>

<implementation>
Steps:
1. First, delete all old test files listed above (check each exists before deleting)
2. Read the route files, schemas, and constants to understand exact endpoint paths, request formats, and expected responses
3. Write `test-api-comprehensive.py` following the scenarios above
4. Ensure the script handles the case where the server isn't running (connection error) with a clear message

Key implementation details:
- Use `requests` library (standard, no async needed for test script)
- Store tokens in a dict keyed by student identifier for easy reuse
- Store complaint IDs as they're created for use in later operations
- Generate test images with Pillow (import PIL) — a simple solid-color image is fine
- Use `argparse` for the `--base-url` option
- Print separators between sections for readability
- If an authority doesn't exist yet, the script should handle that (either create one via admin endpoint or note it in output)

Do NOT:
- Use pytest or any test framework — this is a standalone script
- Use assert statements — print responses and let the human reader evaluate
- Use async/await — keep it simple with synchronous requests
- Skip error responses — print them too, they're informative
</implementation>

<verification>
Before declaring complete:

1. Verify all old test files have been deleted (only files that existed)
2. Verify `test-api-comprehensive.py` exists at the project root
3. Read through the script to confirm:
   - All 13 scenario sections (a through m) are implemented
   - Each prints the full JSON response with status code
   - Tokens are properly stored and reused
   - Complaint IDs are stored and referenced correctly
   - Error handling wraps each section so failures don't stop the script
   - The output format is clean and readable
4. Verify the script has no syntax errors by checking it can be parsed: `python -c "import ast; ast.parse(open('test-api-comprehensive.py').read())"`
</verification>

<success_criteria>
- All old test files deleted from project root
- `test-api-comprehensive.py` created with all 13 scenario sections
- Script prints actual API responses (not pass/fail)
- Each operation clearly labeled with endpoint, status code, and pretty-printed JSON
- Script handles server-not-running gracefully
- Script handles individual operation failures without stopping
- Authority login works (either using pre-existing authority or creating one)
- Summary printed at end showing all operations and their HTTP status codes
- Script runs successfully with `python test-api-comprehensive.py` against a running server
</success_criteria>
