# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Ask Houston AI is a natural language data exploration tool for Houston's 311 incident data (with plans to expand to 911 calls, real estate, and demographics). Users ask questions in plain English, which are converted to SQL queries via an LLM, then results are displayed in a tabular format.

## Tech Stack

- **Frontend**: SvelteKit (Svelte 5) with TypeScript
- **Backend**: FastAPI (Python) serving as API gateway
- **AI/LLM**: Ollama (local LLM server) for natural language to SQL translation
- **Database**: PostgreSQL 15 with PostGIS extension
- **Data Loading**: Python ETL scripts that fetch Houston 311 data from city data portal
- **Containerization**: Docker Compose orchestrating all services

## Development Commands

### Starting the Application

```bash
# Start all services (PostgreSQL, loader, FastAPI backend, SvelteKit frontend)
docker-compose up

# Start specific services
docker-compose up postgres
docker-compose up app
docker-compose up frontend
```

The application will be available at http://localhost:4173 (frontend) and http://localhost:8000 (backend API).

### Frontend Development

```bash
cd frontend

# Install dependencies
npm install

# Run development server (with hot reload)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type checking
npm run check

# Type checking with watch mode
npm run check:watch
```

### Backend Development

The FastAPI backend runs in the `app/` directory:

```bash
cd app

# Install Python dependencies
pip install -r requirements.txt

# Run the server (if running outside Docker)
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Architecture

### Data Flow

1. **User Input**: User enters natural language question in SvelteKit frontend
2. **Frontend Request**: Frontend proxies request to `/ask?q={question}` endpoint
3. **Prompt Building**: `base_prompt_builder.py` queries database to build dynamic prompt with:
   - Table schema (columns from houston_311.incidents)
   - All distinct values for categorical fields (status, incident_case_type, council_district, etc.)
4. **LLM Processing**: Prompt + question sent to Ollama server which returns SQL query
5. **SQL Extraction**: Regex extracts SQL from LLM response, cleans markdown/explanations
6. **Query Execution**: SQL executed against PostgreSQL database
7. **Response**: Results returned as JSON to frontend and displayed in table

### Database Schema

Single table: `houston_311.incidents` with 49 columns including:
- Identifiers: case_365_number, case_number (PK)
- Location: incident_address, latitude, longitude, council_district, customer_super_neighborhood
- Categorization: incident_case_type, department, division, ava_case_type
- Status: status, created_date_local, closed_date, resolution_notes
- Metadata: channel, service_area, management_district

Database initialization happens via `postgres/init.sql` which creates the schema and table structure.

### Component Structure

**Frontend** (`frontend/src/`):
- `routes/+page.svelte`: Main UI - input textarea, query button, results table
- Uses Vite proxy to forward `/ask` requests to FastAPI backend

**Backend** (`app/`):
- `main.py`: FastAPI app with `/ask` endpoint, CORS middleware
- `base_prompt_builder.py`: Dynamically builds LLM prompt with schema metadata (cached via `@lru_cache`)
- `base_prompt.txt`: Base system prompt template for SQL generation
- `config.py`: Configuration for Ollama model and host

**Data Loader** (`loader/`):
- `load_311_data.py`: Downloads Houston 311 data from city portal (last 4 years), parses pipe-delimited format, inserts into PostgreSQL
- `run_loader_once.sh`: Shell script that waits for PostgreSQL and runs loader once
- `wait-for-it.sh`: Utility to wait for PostgreSQL availability

### Key Design Patterns

- **Dynamic Prompt Construction**: The system queries the database at startup to get all distinct categorical values, which are injected into the LLM prompt. This helps the LLM generate more accurate SQL queries with valid filter values.
- **SQL Extraction**: LLM responses are parsed with regex to extract just the SQL query, handling cases where the LLM includes explanatory text or markdown formatting.
- **Schema-Qualified Queries**: The prompt explicitly instructs the LLM to use `houston_311.incidents` (not just `incidents`) to avoid ambiguity.

## Important Notes

- The `base_prompt_builder` uses `@lru_cache` to avoid rebuilding the prompt on every request - only queries database once per app lifecycle
- Frontend uses Vite's proxy configuration (`vite.config.ts`) to route `/ask` requests to the FastAPI backend
- Data loader runs once on startup via Docker Compose, fetching data from Houston's public data portal for years 2022-2025
- CORS is wide open (`allow_origins=["*"]`) - should be restricted in production
- Database credentials are hardcoded for development - should use environment variables in production
