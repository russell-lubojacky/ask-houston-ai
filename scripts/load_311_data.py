import os
import requests
import psycopg2
import csv
from io import StringIO

url = "https://hfdapp.houstontx.gov/311/311-CRIS-Public-Data-Extract-D365-YTD-compressed-2025.txt"
# https://hfdapp.houstontx.gov/311/311-CRIS-Public-Data-Extract-D365-YTD-compressed-2024.txt
# https://hfdapp.houstontx.gov/311/311-CRIS-Public-Data-Extract-D365-YTD-compressed-2023.txt
# https://hfdapp.houstontx.gov/311/311-CRIS-Public-Data-Extract-D365-YTD-compressed-2022.txt

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", "5432"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", "postgres")
    dbname=os.getenv("DB_NAME", "houston_311")
)

cur = conn.cursor()
print("Downloading 311 data...")
response = requests.get(url)
tsv_data = response.text

reader = csv.reader(StringIO(tsv_data), delimiter="|")
headers = next(reader)

for row in reader:
    cur.execute("""
        INSERT INTO houston_311.incidents (case_365_number, case_number, incident_address, latitude, longitude, status, created_date_local, closed_date, title, incident_case_type, sla_time, resolve_by_time, service_area, council_district, key_map, department, division, ava_case_type, state_code, state_code_name, sla_start_time, x, y, incident_street, incident_city, incident_state, zip_code, taxid, created_date_utc, customer_super_neighborhood, management_district, garbage_route, garbage_day, swm_quadrant, recycling_route, recycling_day, recycling_quadrant, recycling_areas, heavy_trash_day, heavy_trash_quadrant, queue, etj, sla_name, channel, extract_date, latest_case_notes, sample_case_conflicts_notes, description, resolution_notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
    """, row[:49])

conn.commit()
cur.close()
conn.close()
print("Data load complete.")
