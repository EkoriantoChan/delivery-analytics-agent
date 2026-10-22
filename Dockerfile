FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files and source code
COPY src/ ./src/
COPY app.py .
COPY docs/ ./docs/
COPY start.sh .

# Ensure start script has executable permissions and unix line endings
RUN chmod +x start.sh && sed -i 's/\r$//' start.sh

# Create persistent storage directory for SQLite database
RUN mkdir -p /app/data && chmod 777 /app/data

# Expose ports for Hugging Face Spaces (7860), API (8000), and local Streamlit (8501)
EXPOSE 7860 8000 8501

# Default command for Hugging Face Spaces / standalone container
CMD ["./start.sh"]
