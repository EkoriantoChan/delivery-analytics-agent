#!/bin/bash
set -e

# Start FastAPI backend in background on port 8000
echo "Starting FastAPI backend on port 8000..."
uvicorn src.api:app --host 0.0.0.0 --port 8000 &

# Wait for API to become healthy
until curl -s http://127.0.0.1:8000/healthz > /dev/null; do
    echo "Waiting for backend API to initialize..."
    sleep 1
done
echo "Backend API is online and healthy!"

# Determine UI port (Hugging Face Spaces uses 7860 by default)
UI_PORT="${PORT:-7860}"
echo "Starting Streamlit UI on port ${UI_PORT}..."
exec streamlit run app.py --server.port "${UI_PORT}" --server.address 0.0.0.0
