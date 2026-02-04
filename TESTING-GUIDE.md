# CampusVoice - Testing Guide

This guide provides step-by-step instructions for testing all three critical features implemented in the CampusVoice backend rewrite.

---

## Prerequisites

1. **Start the application**:
   ```bash
   python main.py
   ```

2. **Application should be running on**: `http://localhost:8000`

3. **API Documentation**: `http://localhost:8000/docs` (Swagger UI)

4. **Test Accounts** (create if needed):
   - Student: Any valid student account
   - Authority: Any valid authority account
   - Admin: Authority with `authority_type="Admin"`

---

## Feature 1: LLM-Driven Image Requirements

### Test 1.1: Infrastructure Complaint Requires Image

**Endpoint**: `POST /complaints/submit`

**Request** (multipart/form-data, NO image):
```bash
curl -X POST "http://localhost:8000/complaints/submit" \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN" \
  -F "category_id=1" \
  -F "original_text=The ceiling fan in hostel room 204 is broken and hanging dangerously from the ceiling" \
  -F "visibility=Public"
```

**Expected Result**:
- HTTP Status: `400 Bad Request`
- Response Body:
```json
{
  "success": false,
  "error": "Image required",
  "reason": "This complaint requires supporting images. Infrastructure issue requiring visual evidence. Please upload at least one image showing photo showing the broken item clearly.",
  "image_required": true
}
```

**Verification**:
- ✅ Complaint is NOT created in database
- ✅ Clear error message explaining why image is needed
- ✅ User knows exactly what to do (upload image)

---

### Test 1.2: Infrastructure Complaint WITH Image (Success)

**Request** (multipart/form-data, WITH image):
```bash
curl -X POST "http://localhost:8000/complaints/submit" \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN" \
  -F "category_id=1" \
  -F "original_text=The ceiling fan in hostel room 204 is broken and hanging dangerously" \
  -F "visibility=Public" \
  -F "image=@test_image.jpg"
```

**Expected Result**:
- HTTP Status: `201 Created`
- Response Body (excerpt):
```json
{
  "id": "uuid-here",
  "status": "Submitted",
  "message": "Complaint submitted successfully",
  "priority": "High",
  "has_image": true,
  "image_verified": true,
  "image_was_required": true,
  "image_requirement_reasoning": "Infrastructure issue requiring visual evidence"
}
```

**Verification**:
- ✅ Complaint created successfully
- ✅ Image stored and verified
- ✅ Response shows `image_was_required=true`
- ✅ Priority is appropriate (High/Critical for safety issues)

---

### Test 1.3: Policy/Abstract Complaint (Image NOT Required)

**Request** (multipart/form-data, NO image):
```bash
curl -X POST "http://localhost:8000/complaints/submit" \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN" \
  -F "category_id=1" \
  -F "original_text=The hostel curfew timing of 10 PM should be extended to 11 PM on weekends for better convenience" \
  -F "visibility=Public"
```

**Expected Result**:
- HTTP Status: `201 Created`
- Response Body (excerpt):
```json
{
  "id": "uuid-here",
  "status": "Submitted",
  "message": "Complaint submitted successfully",
  "priority": "Low",
  "has_image": false,
  "image_was_required": false,
  "image_requirement_reasoning": "No strong visual evidence requirements detected"
}
```

**Verification**:
- ✅ Complaint created successfully WITHOUT image
- ✅ Response shows `image_was_required=false`
- ✅ No error about missing image

---

## Feature 2: Spam Rejection Flow

### Test 2.1: Spam Content is Rejected

**Request**:
```bash
curl -X POST "http://localhost:8000/complaints/submit" \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN" \
  -F "category_id=1" \
  -F "original_text=This is just a test dummy complaint asdf qwerty xyz" \
  -F "visibility=Public"
```

**Expected Result**:
- HTTP Status: `400 Bad Request`
- Response Body:
```json
{
  "success": false,
  "error": "Complaint marked as spam/abusive",
  "reason": "Complaint marked as spam/abusive: Appears to be test/dummy content",
  "is_spam": true
}
```

**Verification in Database**:
```sql
-- Connect to PostgreSQL (password: 110305)
SELECT * FROM complaints WHERE original_text LIKE '%test dummy%';
-- Should return 0 rows (spam NOT stored)

SELECT * FROM complaints ORDER BY submitted_at DESC LIMIT 5;
-- Spam complaint should NOT appear in recent complaints
```

**Verification**:
- ✅ HTTP 400 error returned
- ✅ Clear spam error message
- ✅ Complaint NOT created in database
- ✅ No "Spam" status complaints in database

---

### Test 2.2: Abusive Content is Rejected

**Request**:
```bash
curl -X POST "http://localhost:8000/complaints/submit" \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN" \
  -F "category_id=4" \
  -F "original_text=The stupid warden is an idiot and should be fired. This is ridiculous nonsense." \
  -F "visibility=Public"
```

**Expected Result**:
- HTTP Status: `400 Bad Request`
- Response Body:
```json
{
  "success": false,
  "error": "Complaint marked as spam/abusive",
  "reason": "Complaint marked as spam/abusive: Contains abusive or offensive language targeting individuals",
  "is_spam": true
}
```

**Verification**:
- ✅ Abusive complaint rejected
- ✅ NOT stored in database
- ✅ Clear error message

---

### Test 2.3: Multiple Spam Attempts Lead to Account Suspension

**Step 1**: Submit 3 spam complaints with same student account

**Request 1, 2, 3**:
```bash
# Run this command 3 times
curl -X POST "http://localhost:8000/complaints/submit" \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN" \
  -F "category_id=1" \
  -F "original_text=test spam complaint number X" \
  -F "visibility=Public"
```

**Expected Results**:
- First attempt: HTTP 400, spam rejection
- Second attempt: HTTP 400, spam rejection
- **Third attempt**: HTTP 400, spam rejection + **account suspended message**

**Response after 3rd attempt**:
```json
{
  "success": false,
  "error": "Complaint marked as spam/abusive",
  "reason": "Complaint marked as spam/abusive: Test/dummy content. Account temporarily suspended due to multiple violations.",
  "is_spam": true
}
```

**Step 2**: Try to submit legitimate complaint after suspension

**Request**:
```bash
curl -X POST "http://localhost:8000/complaints/submit" \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN" \
  -F "category_id=1" \
  -F "original_text=The library WiFi is not working properly" \
  -F "visibility=Public"
```

**Expected Result**:
- HTTP Status: `400 Bad Request`
- Response: "Account suspended: Multiple spam attempts. Ban expires on [DATE]."

**Verification in Database**:
```sql
SELECT * FROM spam_blacklist WHERE student_roll_no = 'YOUR_ROLL_NO';
-- Should show 1 row with is_permanent=false, expires_at set to 7 days from now
```

**Verification**:
- ✅ After 3 spam attempts, account is suspended
- ✅ Ban duration is 7 days (temporary)
- ✅ Blacklist entry created in database
- ✅ Even legitimate complaints are blocked during suspension

---

## Feature 3: Partial Anonymity System

### Test 3.1: Authority Viewing Non-Spam Complaint (Student Info Hidden)

**Step 1**: Create a legitimate (non-spam) complaint as student

**Request**:
```bash
curl -X POST "http://localhost:8000/complaints/submit" \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN" \
  -F "category_id=1" \
  -F "original_text=The hostel mess food quality has deteriorated recently" \
  -F "visibility=Public"
```

Note the complaint ID from response.

**Step 2**: Authority views the complaint

**Request**:
```bash
curl -X GET "http://localhost:8000/authorities/complaints/YOUR_COMPLAINT_ID" \
  -H "Authorization: Bearer YOUR_AUTHORITY_TOKEN"
```

**Expected Result**:
```json
{
  "id": "complaint-uuid",
  "rephrased_text": "Issue: The quality of food served in the hostel mess...",
  "status": "Raised",
  "priority": "Medium",
  "is_spam": false,
  "student_roll_no": "Hidden (non-spam)",
  "student_name": "Hidden (non-spam)",
  "student_email": "Hidden (non-spam)",
  "student_gender": null,
  "student_stay_type": null,
  "student_year": null,
  "student_department": null
}
```

**Verification**:
- ✅ Complaint details visible
- ✅ Student personal information HIDDEN
- ✅ All student fields show "Hidden (non-spam)" or null
- ✅ Authority can still work on complaint without knowing student identity

---

### Test 3.2: Authority Viewing Spam Complaint (Student Info Revealed)

**Step 1**: Create a complaint and mark it as spam (via admin)

Option A - Admin marks legitimate complaint as spam:
```bash
# First create a complaint, then have admin mark it as spam
# Use admin endpoints to flag complaint as spam
```

Option B - Use test database entry:
```sql
-- Connect to PostgreSQL
INSERT INTO complaints (
  id, student_roll_no, category_id, original_text, rephrased_text,
  visibility, status, is_marked_as_spam, spam_reason,
  priority, priority_score, submitted_at, updated_at
) VALUES (
  gen_random_uuid(),
  'YOUR_STUDENT_ROLL_NO',
  1,
  'Spam test content',
  'Spam test content',
  'Public',
  'Spam',
  true,
  'Test spam entry',
  'Low',
  10.0,
  NOW(),
  NOW()
);
```

**Step 2**: Authority views the spam complaint

**Request**:
```bash
curl -X GET "http://localhost:8000/authorities/complaints/SPAM_COMPLAINT_ID" \
  -H "Authorization: Bearer YOUR_AUTHORITY_TOKEN"
```

**Expected Result**:
```json
{
  "id": "complaint-uuid",
  "rephrased_text": "Spam test content",
  "status": "Spam",
  "priority": "Low",
  "is_spam": true,
  "spam_reason": "Test spam entry",
  "student_roll_no": "22CS231",
  "student_name": "John Doe",
  "student_email": "john.doe@college.edu",
  "student_gender": "Male",
  "student_stay_type": "Hostel",
  "student_year": "3rd Year",
  "student_department": "Computer Science & Engineering"
}
```

**Verification**:
- ✅ Complaint marked as spam
- ✅ Full student information VISIBLE to authority
- ✅ All student fields populated
- ✅ Authority can identify repeat spam offender

---

### Test 3.3: Admin Viewing Any Complaint (Full Access)

**Request** (admin token, any complaint):
```bash
curl -X GET "http://localhost:8000/authorities/complaints/ANY_COMPLAINT_ID" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Expected Result** (even for non-spam complaints):
```json
{
  "id": "complaint-uuid",
  "rephrased_text": "...",
  "status": "Raised",
  "priority": "Medium",
  "is_spam": false,
  "student_roll_no": "22CS231",
  "student_name": "John Doe",
  "student_email": "john.doe@college.edu",
  "student_gender": "Male",
  "student_stay_type": "Hostel",
  "student_year": "3rd Year",
  "student_department": "Computer Science & Engineering"
}
```

**Verification**:
- ✅ Admin sees ALL student information
- ✅ Works for both spam and non-spam complaints
- ✅ No information hidden

---

### Test 3.4: Authority Viewing Complaint List (Partial Anonymity)

**Request**:
```bash
curl -X GET "http://localhost:8000/authorities/complaints?limit=10" \
  -H "Authorization: Bearer YOUR_AUTHORITY_TOKEN"
```

**Expected Result**:
```json
{
  "complaints": [
    {
      "id": "uuid-1",
      "status": "Raised",
      "is_spam": false,
      "student_roll_no": null,
      "student_name": null
    },
    {
      "id": "uuid-2",
      "status": "Spam",
      "is_spam": true,
      "student_roll_no": "22CS999",
      "student_name": "Spammer Name"
    }
  ],
  "total": 2,
  "page": 1
}
```

**Verification**:
- ✅ Non-spam complaints show `null` for student fields
- ✅ Spam complaints show full student info
- ✅ Partial anonymity applied consistently across list

---

## Combined Feature Test: Complete Flow

### Scenario: Student submits infrastructure complaint with all checks

**Step 1**: Student submits complaint without image (infrastructure issue)

**Request**:
```bash
curl -X POST "http://localhost:8000/complaints/submit" \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN" \
  -F "category_id=1" \
  -F "original_text=The AC unit in hostel room 305 is leaking water and creating a puddle on the floor" \
  -F "visibility=Public"
```

**Expected**: HTTP 400 - Image required

---

**Step 2**: Student uploads image and resubmits

**Request**:
```bash
curl -X POST "http://localhost:8000/complaints/submit" \
  -H "Authorization: Bearer YOUR_STUDENT_TOKEN" \
  -F "category_id=1" \
  -F "original_text=The AC unit in hostel room 305 is leaking water and creating a puddle on the floor" \
  -F "visibility=Public" \
  -F "image=@leaking_ac.jpg"
```

**Expected**: HTTP 201 - Complaint created with image

---

**Step 3**: Authority views complaint (non-spam)

**Request**:
```bash
curl -X GET "http://localhost:8000/authorities/complaints/COMPLAINT_ID" \
  -H "Authorization: Bearer YOUR_AUTHORITY_TOKEN"
```

**Expected**: Student info hidden (partial anonymity)

---

**Step 4**: Admin views same complaint

**Request**:
```bash
curl -X GET "http://localhost:8000/authorities/complaints/COMPLAINT_ID" \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN"
```

**Expected**: Full student info visible

---

**Step 5**: Authority updates status

**Request**:
```bash
curl -X PUT "http://localhost:8000/authorities/complaints/COMPLAINT_ID/status" \
  -H "Authorization: Bearer YOUR_AUTHORITY_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "status": "In Progress",
    "reason": "Maintenance team dispatched to Room 305"
  }'
```

**Expected**: HTTP 200 - Status updated, notification sent to student

---

## Database Verification Queries

### Check complaints table
```sql
-- Connect: psql -U postgres -d campusvoice -W
-- Password: 110305

-- View recent complaints (should NOT include spam)
SELECT
  id,
  student_roll_no,
  original_text,
  status,
  is_marked_as_spam,
  submitted_at
FROM complaints
ORDER BY submitted_at DESC
LIMIT 10;

-- Count complaints by status
SELECT status, COUNT(*)
FROM complaints
GROUP BY status;

-- Should NOT have any spam status complaints if spam rejection works
```

### Check spam blacklist
```sql
-- View blacklisted students
SELECT
  student_roll_no,
  reason,
  spam_count,
  is_permanent,
  expires_at,
  blacklisted_at
FROM spam_blacklist;

-- Should show students with 3+ spam attempts
```

### Check image storage
```sql
-- Complaints with images
SELECT
  id,
  student_roll_no,
  image_filename,
  image_size,
  image_verified,
  image_verification_status
FROM complaints
WHERE image_data IS NOT NULL;
```

---

## Expected Behavior Summary

### LLM Image Requirements
- ✅ Infrastructure issues → Image REQUIRED
- ✅ Policy/abstract issues → Image OPTIONAL
- ✅ Clear error messages when required image missing
- ✅ Complaints with images verified by LLM

### Spam Rejection
- ✅ Spam detected BEFORE database creation
- ✅ Spam complaints NEVER stored
- ✅ Clear error responses with reasoning
- ✅ Automatic blacklisting after 3 attempts
- ✅ Temporary 7-day suspensions

### Partial Anonymity
- ✅ Admin: All student info visible
- ✅ Authority (non-spam): Student info HIDDEN
- ✅ Authority (spam): Student info REVEALED
- ✅ Consistent across list and detail views

---

## Troubleshooting

### Issue: "Groq API Error"
**Solution**: Check `GROQ_API_KEY` in `.env` file, verify API quota

### Issue: "Image required but I uploaded one"
**Solution**: Ensure using multipart/form-data, check file size < 5MB

### Issue: "Student info visible when it should be hidden"
**Solution**: Verify authority is not admin, check complaint `is_marked_as_spam` field

### Issue: "Spam complaint was created in database"
**Solution**: Check for exceptions during complaint creation, verify spam check runs first

---

## Testing Checklist

Before declaring feature complete:

**LLM Image Requirements**:
- [ ] Infrastructure complaint without image → rejected
- [ ] Infrastructure complaint with image → accepted
- [ ] Abstract complaint without image → accepted
- [ ] Error messages are clear and helpful

**Spam Rejection**:
- [ ] Spam text rejected with HTTP 400
- [ ] Spam NOT in database
- [ ] 3 spam attempts → account suspended
- [ ] Suspended account cannot submit even legitimate complaints

**Partial Anonymity**:
- [ ] Authority cannot see student info for non-spam
- [ ] Authority CAN see student info for spam
- [ ] Admin can see all student info
- [ ] Works in both list and detail views

**Integration**:
- [ ] Complete flow works end-to-end
- [ ] No breaking changes to existing functionality
- [ ] All endpoints return proper HTTP status codes
- [ ] Error messages are user-friendly

---

**Test Duration**: Approximately 30-45 minutes for complete test suite
**Tools Needed**: curl, PostgreSQL client, Postman (optional)
**Test Environment**: Local development server (`http://localhost:8000`)
