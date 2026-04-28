# ──────────────────────────────────────────────────
# Dockerfile for Raspberry Pi (Cloud-Only Mode)
# Uses Python 3.11 + lightweight dependencies
# ──────────────────────────────────────────────────

FROM python:3.11-slim-bookworm

# System dependencies for OpenCV (headless)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libopenblas-dev \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy cloud requirements first (Docker caching)
COPY requirements-cloud.txt .
RUN pip install --no-cache-dir -r requirements-cloud.txt

# Copy project code
COPY . .

# Create data directories
RUN mkdir -p data/photos data/db

# Expose port
EXPOSE 8000

# Start backend server
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
