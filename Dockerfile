# Multi-stage build for Sentio
# Stage 1: Build Frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ ./

# Build frontend
RUN npm run build

# Stage 2: Python Backend with Frontend static files
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend files
COPY backend/ ./

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Copy built frontend from stage 1
COPY --from=frontend-builder /app/frontend/dist ./static

# Create directories for data persistence
RUN mkdir -p /app/data /app/surveys

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV STATIC_FILES_DIR=/app/static

# Expose port (Heroku sets PORT dynamically)
EXPOSE 8000

# Run the application
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
