FROM python:3.11-slim

WORKDIR /app

# Install system-level packages for psycopg2
RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app code
COPY . .

# No CMD — docker-compose will handle it (via: command: ["python", "app.py"])
