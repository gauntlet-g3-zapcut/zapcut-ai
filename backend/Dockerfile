FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Copy startup scripts
COPY start.sh start-worker.sh ./
RUN chmod +x start.sh start-worker.sh

# Default to API startup (can be overridden in fly.toml)
CMD ["./start.sh"]

