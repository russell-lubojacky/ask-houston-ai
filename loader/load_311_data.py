import os
import requests
import psycopg2
import csv
import sys
from io import StringIO

csv.field_size_limit(sys.maxsize)

# create an array of the last 4 years
years = [2025, 2024, 2023, 2022]
urls = [f"https://hfdapp.houstontx.gov/311/311-CRIS-Public-Data-Extract-D365-YTD-compressed-{year}.txt" for year in years]

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "postgres"),
    port=os.getenv("DB_PORT", "5432"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "postgres"),
    dbname=os.getenv("DB_NAME", "houston_311_db")
)

cur = conn.cursor()
count = 0
for url in urls:
    print("Downloading 311 data...")
    response = requests.get(url)
    tsv_data = response.text.replace('\r\n', '\n')

    lines = tsv_data.splitlines()
    # Find the first line that looks like a header (contains the expected delimiter)
    for i, line in enumerate(lines):
        if "365 Case Number" in line and "|" in line:
            header_index = i
            break
        
    clean_lines = [line.replace('"', '') for line in lines[header_index:]]
    reader = csv.reader(clean_lines, delimiter="|", quoting=csv.QUOTE_NONE)
    headers = next(reader)

    for row in reader:
        # Check if the row has the expected number of columns
        if len(row) != len(headers):
            print(f"Row length mismatch: expected {len(headers)}, got {len(row)}")
            continue  # Skip this row if it doesn't match

        try:
            cur.execute("""
                INSERT INTO houston_311.incidents (case_365_number, case_number, incident_address, latitude, longitude, status, created_date_local, closed_date, title, incident_case_type, sla_time, resolve_by_time, service_area, council_district, key_map, department, division, ava_case_type, state_code, state_code_name, sla_start_time, x, y, incident_street, incident_city, incident_state, zip_code, taxid, created_date_utc, customer_super_neighborhood, management_district, garbage_route, garbage_day, swm_quadrant, recycling_route, recycling_day, recycling_quadrant, recycling_areas, heavy_trash_day, heavy_trash_quadrant, queue, etj, sla_name, channel, extract_date, latest_case_notes, sample_case_conflicts_notes, description, resolution_notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT DO NOTHING;
            """, row[:49])

            count += 1
            if count % 1000 == 0:
                print(f"Inserted {count} rows...")
        except Exception as e:
            print(f"Error inserting row {count}: {e}")
            continue  # Skip this row if there's an error

print(f"Total rows inserted: {count}")

conn.commit()
cur.close()
conn.close()
print("Data load complete.")
