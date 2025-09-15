# Use official Python slim image
FROM python:3.11-slim

ENV TZ="Etc/UTC"

# Install system dependencies
RUN apt-get update && apt-get install -y procps && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ /app/
COPY config/config.yaml /config_sample.yaml

# Set up entrypoint
COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Expose Streamlit port
EXPOSE 8501

# Set default volumes
VOLUME ["/data", "/config"]

# Start application
ENTRYPOINT ["/app/entrypoint.sh"]
