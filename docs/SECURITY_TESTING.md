# Security Safeguards Testing

This document outlines the security safeguards implemented in Ask Houston AI and how to test them.

## Implemented Safeguards

### 1. Frontend Input Validation (`frontend/src/routes/+page.svelte`)
- ✅ Empty query detection
- ✅ Maximum length check (1000 characters)
- ✅ Suspicious pattern detection (DROP, DELETE, INSERT, UPDATE, TRUNCATE, ALTER)
- ✅ Character counter with visual warning at 900+ characters
- ✅ Better error message display from backend

### 2. Enhanced LLM Prompt (`app/base_prompt.txt`)
- ✅ Topic restriction instructions (only 311 incident data)
- ✅ INVALID_TOPIC response for off-topic questions
- ✅ Explicit prohibition of destructive SQL operations
- ✅ Examples of valid and invalid questions

### 3. Intent Classification (`app/main.py` - `check_question_intent()`)
- ✅ Pre-validates questions are about 311 data before SQL generation
- ✅ Uses separate LLM call to classify question intent
- ✅ Fails open (allows request if intent check fails) for availability
- ✅ Clear error messages for invalid questions

### 4. SQL Query Validation (`app/main.py` - `validate_sql()`)
- ✅ Detects INVALID_TOPIC responses from LLM
- ✅ Blocks dangerous SQL keywords (DROP, DELETE, UPDATE, INSERT, ALTER, etc.)
- ✅ Blocks SQL injection attempts (UNION, --, /*, etc.)
- ✅ Ensures only SELECT or WITH (CTE) queries
- ✅ Validates only houston_311.incidents table is accessed
- ✅ Blocks system table access (information_schema, pg_catalog)

### 5. Database Permissions (`postgres/init.sql`)
- ✅ Read-only user (readonly_311) created
- ✅ User can only SELECT from houston_311.incidents
- ✅ No CREATE, DROP, UPDATE, DELETE, INSERT permissions
- ✅ No access to other schemas or system tables

### 6. Backend Endpoint Protection (`app/main.py` - `/ask` endpoint)
- ✅ Input length validation (max 1000 chars)
- ✅ Empty query detection
- ✅ Intent classification check
- ✅ SQL validation before execution
- ✅ Proper error handling and messaging

## Testing Scenarios

### Test 1: Valid 311 Questions (Should PASS)
```
✅ "Show me all pothole incidents"
✅ "How many graffiti reports are open?"
✅ "List incidents in District 5"
✅ "What are the most common incident types?"
```

### Test 2: Off-Topic Questions (Should FAIL)
```
❌ "What's the weather today?"
❌ "Tell me about Houston sports teams"
❌ "What is 2+2?"
❌ "Show me all database tables"
```

### Test 3: SQL Injection Attempts (Should FAIL)
```
❌ "'; DROP TABLE incidents; --"
❌ "1' UNION SELECT * FROM pg_tables--"
❌ "Show potholes'; DELETE FROM houston_311.incidents;--"
❌ "' OR 1=1--"
```

### Test 4: Destructive Operations (Should FAIL)
```
❌ "DROP TABLE houston_311.incidents"
❌ "DELETE FROM houston_311.incidents WHERE 1=1"
❌ "UPDATE houston_311.incidents SET status='Closed'"
❌ "INSERT INTO houston_311.incidents VALUES (...)"
❌ "TRUNCATE TABLE houston_311.incidents"
```

### Test 5: System Table Access (Should FAIL)
```
❌ "SELECT * FROM information_schema.tables"
❌ "SELECT * FROM pg_catalog.pg_tables"
❌ "SHOW TABLES"
```

### Test 6: Input Length (Should FAIL)
```
❌ Query with 1001+ characters
```

### Test 7: Empty/Invalid Input (Should FAIL)
```
❌ Empty query
❌ Whitespace-only query
```

## Manual Testing Instructions

1. **Start the application:**
   ```bash
   docker compose up
   ```

2. **Open the frontend:**
   Navigate to http://localhost:4173

3. **Test each scenario above:**
   - Enter the test queries in the textarea
   - Click "Ask" button
   - Verify the expected behavior (pass/fail)

4. **Check error messages:**
   - Off-topic questions should show: "Your question doesn't appear to be about Houston 311 incident data..."
   - SQL validation failures should show: "Security validation failed: ..."
   - Frontend validation should show specific error for the issue

5. **Verify database permissions:**
   ```bash
   # Connect as readonly_311 user
   docker compose exec postgres psql -U readonly_311 -d houston_311_db

   # Try SELECT (should work)
   SELECT COUNT(*) FROM houston_311.incidents;

   # Try DELETE (should fail with permission denied)
   DELETE FROM houston_311.incidents WHERE 1=1;

   # Try DROP (should fail with permission denied)
   DROP TABLE houston_311.incidents;
   ```

## Expected Security Behavior

### Defense in Depth
The system implements multiple layers of security:

1. **Frontend** catches obvious issues early (better UX)
2. **Intent Classification** prevents wasting resources on off-topic questions
3. **SQL Validation** catches injection attempts and validates query structure
4. **LLM Prompt** instructs model to refuse dangerous operations
5. **Database Permissions** provides final failsafe - even if malicious SQL is generated, it cannot execute

### Error Message Strategy
- User-friendly messages for legitimate mistakes
- Generic "validation failed" messages for attack attempts
- No disclosure of internal system details
- Specific guidance for valid question topics

## Production Recommendations

Before deploying to production, consider:

1. **Environment Variables:** Move credentials to .env file
2. **CORS:** Restrict allowed origins in FastAPI middleware
3. **Rate Limiting:** Add rate limiting to /ask endpoint
4. **Logging:** Log all failed validation attempts for security monitoring
5. **SSL/TLS:** Enable HTTPS for all communications
6. **Firewall:** Restrict database access to application servers only
7. **Secret Management:** Use proper secret management (AWS Secrets Manager, etc.)
8. **Regular Updates:** Keep dependencies up-to-date for security patches

## Monitoring & Alerts

Consider adding monitoring for:
- Failed validation attempts (potential attacks)
- Unusual query patterns
- Database connection failures
- High error rates
- Slow query performance
