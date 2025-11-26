import psycopg2
import os
from functools import lru_cache

@lru_cache(maxsize=1)
def base_prompt_builder():
    # WARNING: Change DB_PASSWORD in production! Use .env file.
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "houston_311_db"),
        user=os.getenv("DB_USER", "readonly_311"),
        password=os.getenv("DB_PASSWORD", "dev_readonly_password_CHANGE_IN_PRODUCTION")
    )
    cur = conn.cursor()

    cur.execute("""
        SELECT DISTINCT status FROM houston_311.incidents ORDER BY status;
    """)
    status_value = [row[0] for row in cur.fetchall() if row[0]]

    cur.execute("""
        SELECT DISTINCT incident_case_type FROM houston_311.incidents ORDER BY incident_case_type;
    """)
    incident_case_type_value = [row[0] for row in cur.fetchall() if row[0]]

    cur.execute("""
        SELECT DISTINCT service_area FROM houston_311.incidents ORDER BY service_area;
    """)
    service_area_value = [row[0] for row in cur.fetchall() if row[0]]

    cur.execute("""
        SELECT DISTINCT council_district FROM houston_311.incidents ORDER BY council_district;
    """)
    council_district_value = [row[0] for row in cur.fetchall() if row[0]]

    cur.execute("""
        SELECT DISTINCT department FROM houston_311.incidents ORDER BY department;
    """)
    department_value = [row[0] for row in cur.fetchall() if row[0]]

    cur.execute("""
        SELECT DISTINCT division FROM houston_311.incidents ORDER BY division;
    """)
    division_value = [row[0] for row in cur.fetchall() if row[0]]

    cur.execute("""
        SELECT DISTINCT ava_case_type FROM houston_311.incidents ORDER BY ava_case_type;
    """)
    ava_case_type_value = [row[0] for row in cur.fetchall() if row[0]]

    cur.execute("""
        SELECT DISTINCT state_code FROM houston_311.incidents ORDER BY state_code;
    """)
    state_code_value = [row[0] for row in cur.fetchall() if row[0]]

    cur.execute("""
        SELECT DISTINCT state_code_name FROM houston_311.incidents ORDER BY state_code_name;
    """)
    state_code_name_value = [row[0] for row in cur.fetchall() if row[0]]

    cur.execute("""
        SELECT DISTINCT customer_super_neighborhood FROM houston_311.incidents ORDER BY customer_super_neighborhood;
    """)
    customer_super_neighborhood_value = [row[0] for row in cur.fetchall() if row[0]]

    cur.execute("""
        SELECT DISTINCT management_district FROM houston_311.incidents ORDER BY management_district;
    """)
    management_district_value = [row[0] for row in cur.fetchall() if row[0]]

    cur.execute("""
        SELECT DISTINCT channel FROM houston_311.incidents ORDER BY channel;
    """)
    channel_value = [row[0] for row in cur.fetchall() if row[0]]

    # Get all column names from the incidents table
    cur.execute("""
        SELECT column_name FROM information_schema.columns
        WHERE table_name = 'incidents'
        ORDER BY ordinal_position;
    """)
    columns = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()

    # Append the base_prompt with the dynamic values
    with open("base_prompt.txt", "r") as f:
        BASE_PROMPT = f.read()

    # Get a few example values instead of all values
    status_examples = status_value[:5] if len(status_value) > 5 else status_value
    incident_type_examples = incident_case_type_value[:10] if len(incident_case_type_value) > 10 else incident_case_type_value

    DYNAMIC_PROMPT = f"""
TABLE: houston_311.incidents (THIS IS THE ONLY TABLE - USE THIS EXACT NAME)

KEY COLUMNS:
- incident_case_type: Type of incident (use ILIKE for matching, e.g., 'Pothole', 'Graffiti')
- created_date_utc: Report date (TEXT type, use >= '2025-01-01' format)
- status: Current status
- incident_address: Full address
- latitude, longitude: Location coordinates
- council_district: District number
- customer_super_neighborhood: Neighborhood name

Common incident types: {', '.join(incident_type_examples[:10])}
Common statuses: {', '.join(status_examples)}

All columns: {', '.join(columns)}
"""

    return BASE_PROMPT + "\n" + DYNAMIC_PROMPT