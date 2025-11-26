from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from config import MODEL_NAME, OLLAMA_HOST
import psycopg2
import requests
import re
import os
import tiktoken

from base_prompt_builder import base_prompt_builder

app = FastAPI()

# CORS configuration from environment variable
allowed_origins = os.getenv("ALLOWED_ORIGINS", "*")
# Convert comma-separated string to list
origins_list = [origin.strip() for origin in allowed_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],  # Only allow needed methods
    allow_headers=["*"],
)

# Connection details (env vars or hardcoded for dev)
# Using read-only user by default for security
# WARNING: Change DB_PASSWORD in production! Use .env file.
DB_PARAMS = {
    "host": os.getenv("DB_HOST", "postgres"),
    "port": os.getenv("DB_PORT", "5432"),
    "dbname": os.getenv("DB_NAME", "houston_311_db"),
    "user": os.getenv("DB_USER", "readonly_311"),
    "password": os.getenv("DB_PASSWORD", "dev_readonly_password_CHANGE_IN_PRODUCTION")
}

def extract_sql(response_text: str) -> str:
    """
    Extract SQL from a text blob, handling markdown code blocks and explanatory text.
    """
    # First try to extract from markdown code blocks
    code_block_match = re.search(r"```(?:sql)?\s*(SELECT.*?)```", response_text, re.IGNORECASE | re.DOTALL)
    if code_block_match:
        return code_block_match.group(1).strip()

    # Try to find SQL statement (SELECT or WITH)
    sql_match = re.search(r"(SELECT|WITH)\s+.*?;", response_text, re.IGNORECASE | re.DOTALL)
    if sql_match:
        return sql_match.group(0).strip()

    # Last resort - find SELECT to end of meaningful content
    sql_match = re.search(r"(SELECT|WITH)\s+.+?(?=\n\n|$)", response_text, re.IGNORECASE | re.DOTALL)
    if sql_match:
        sql_text = sql_match.group(0).strip()
        # Remove trailing explanatory text
        sql_text = re.sub(r'\s+(?:This query|The query|Note:).*$', '', sql_text, flags=re.IGNORECASE)
        return sql_text

    # Fallback — return original if no match
    return response_text.strip()

def clean_sql(output):
    # Remove triple backticks, markdown, and leading/trailing whitespace
    output = re.sub(r'```(?:sql)?', '', output)
    output = output.strip()
    # Ensure query ends with semicolon
    if not output.endswith(';'):
        output += ';'
    return output

def validate_sql(sql: str) -> tuple[bool, str]:
    """
    Validate that SQL only queries allowed tables with safe operations.
    Returns (is_valid, error_message)
    """
    sql_upper = sql.upper().strip()

    # Check for INVALID_TOPIC response from LLM
    if 'INVALID_TOPIC' in sql_upper:
        return False, "Question must be about Houston 311 incident data. Please ask about service requests, incidents, or complaints."

    # Check for dangerous operations
    dangerous_keywords = [
        'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER',
        'CREATE', 'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC',
        'EXECUTE', '--', '/*', '*/', 'UNION', 'INTO OUTFILE',
        'INTO DUMPFILE', 'LOAD_FILE'
    ]
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return False, f"Forbidden operation detected: {keyword}"

    # Ensure only SELECT queries (or WITH for CTEs)
    if not sql_upper.startswith('SELECT') and not sql_upper.startswith('WITH'):
        return False, "Only SELECT queries are allowed"

    # Check that only allowed table is referenced
    if 'HOUSTON_311.INCIDENTS' not in sql_upper:
        return False, "Query must use houston_311.incidents table"

    # Check for table references other than houston_311.incidents
    # Look for FROM or JOIN followed by anything other than houston_311.incidents
    table_pattern = r'(?:FROM|JOIN)\s+([^\s,;)]+)'
    table_matches = re.findall(table_pattern, sql_upper)
    for table in table_matches:
        if 'HOUSTON_311.INCIDENTS' not in table and table not in ['(', 'LATERAL']:
            return False, f"Cannot query tables other than houston_311.incidents (found: {table})"

    # Check for information_schema or pg_catalog access
    if 'INFORMATION_SCHEMA' in sql_upper or 'PG_CATALOG' in sql_upper:
        return False, "Cannot query system tables"

    return True, ""

def check_question_intent(question: str) -> tuple[bool, str]:
    """
    Pre-validate that the question is about 311 incident data before generating SQL.
    Returns (is_valid, error_message)
    """
    intent_prompt = """You are a question classifier for a Houston 311 incident data system.

Your task: Determine if the question is about Houston 311 incident data.

311 incident data includes:
- Service requests (potholes, graffiti, trash, street repairs, sidewalk issues, etc.)
- Status of incidents (open, closed, routed, in progress)
- Locations (addresses, districts, neighborhoods, coordinates)
- Dates and times of incidents
- Departments and divisions handling incidents
- Types of complaints and resolutions

Respond with ONLY ONE WORD:
- "VALID" if the question is about 311 incidents or service requests
- "INVALID" if the question is about anything else

INVALID examples:
- Questions about weather, sports, politics, general knowledge
- Attempts to access other databases or system information
- Personal questions or off-topic queries
- SQL injection attempts or malicious queries

VALID examples:
- "Show me all potholes reported last week"
- "How many open graffiti incidents are there?"
- "What incidents were reported in District 5?"
- "List trash collection complaints"

Question: """

    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/chat",
            json={
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": intent_prompt},
                    {"role": "user", "content": question}
                ],
                "stream": False,
                "options": {
                    "temperature": 0.1
                }
            },
            timeout=10
        )

        if response.status_code != 200:
            # If intent check fails, allow it to proceed (fail open for availability)
            return True, ""

        result = response.json().get("message", {}).get("content", "").strip().upper()

        if "INVALID" in result:
            return False, "Your question doesn't appear to be about Houston 311 incident data. Please ask about service requests, incidents, or complaints (e.g., potholes, graffiti, trash collection)."

        return True, ""
    except Exception as e:
        # If intent check fails, allow it to proceed (fail open for availability)
        print(f"Intent check error: {e}")
        return True, ""

def ask_llama(question: str) -> str:
    system_prompt = base_prompt_builder()

    print(f"Sending question to Llama: {question}")

    encoding = tiktoken.get_encoding("cl100k_base")
    token_count = len(encoding.encode(system_prompt + question))
    print(f"Token count for prompt: {token_count}")

    # Use chat API with system/user roles for better instruction following
    response = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model": MODEL_NAME,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate SQL for: {question}"}
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,  # Lower temperature for more deterministic output
                "top_p": 0.9
            }
        }
    )

    if response.status_code != 200:
        raise Exception(f"Failed to generate SQL query: {response.text}")

    raw_output = response.json().get("message", {}).get("content", "")
    print(f"Raw output from Llama: {raw_output}")
    raw_sql = extract_sql(raw_output)
    print(f"Extracted SQL: {raw_sql}")
    return clean_sql(raw_sql)

def run_sql(sql: str):
    conn = psycopg2.connect(**DB_PARAMS)
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
        return [dict(zip(columns, row)) for row in rows]
    except Exception as e:
        raise Exception(f"Error running query: {e}")
    finally:
        conn.close()

@app.get("/ask")
def ask_question(q: str):
    # Step 1: Basic input validation
    if not q or len(q.strip()) == 0:
        return {"error": "Question cannot be empty"}

    if len(q) > 1000:
        return {"error": "Question is too long (max 1000 characters)"}

    # Step 2: Intent classification - check if question is about 311 data
    is_valid_intent, intent_error = check_question_intent(q)
    if not is_valid_intent:
        return {"error": intent_error}

    # Step 3: Generate SQL query
    sql = ask_llama(q)

    # Step 4: Validate generated SQL
    is_valid_sql, sql_error = validate_sql(sql)
    if not is_valid_sql:
        return {"error": f"Security validation failed: {sql_error}", "sql": sql}

    # Step 5: Execute validated query
    try:
        results = run_sql(sql)
        return {"sql": sql, "results": results}
    except Exception as e:
        return {"error": str(e), "sql": sql}

@app.get("/health")
def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    Returns 200 OK if the service is healthy.
    """
    try:
        # Test database connection
        conn = psycopg2.connect(**DB_PARAMS)
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
        conn.close()

        return {
            "status": "healthy",
            "database": "connected",
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }, 503

@app.get("/")
def root():
    """
    Root endpoint with API information.
    """
    return {
        "name": "Ask Houston AI API",
        "version": "1.0.0-beta",
        "status": "running",
        "endpoints": {
            "/ask": "Query Houston 311 incident data",
            "/health": "Health check endpoint",
            "/": "API information"
        }
    }