FROM python:3.11-slim

# Minimal, pinned runtime for the connector
WORKDIR /app

# Install dependencies first for better layer caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the connector source
COPY . /app/
