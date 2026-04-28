# ──────────────────────────────────────────────────
# Dockerfile for Raspberry Pi (Cloud-Only Mode)
# Uses Python 3.11 + lightweight dependencies
# ──────────────────────────────────────────────────

FROM python:3.11-slim-bookworm

# System dependencies for OpenCV and Compiling
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libopenblas-dev \
    libgl1 \
    libglib2.0-0 \
    libhdf5-dev \
    libhdf5-serial-dev \
    libatlas-base-dev \
    libqt5gui5 \
    libqt5test5 \
    libqt5core5a \
    libwebp-dev \
    libtiff5-dev \
    libopenexr-dev \
    libopenjp2-7-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev \
    libgtk2.0-dev \
    libgtk-3-0 \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Tell pip to use piwheels for much faster installation on ARM
ENV PIP_EXTRA_INDEX_URL=https://www.piwheels.org/simple

# Set working directory
WORKDIR /app

# Copy cloud requirements first (Docker caching)
COPY requirements-cloud.txt .
RUN pip install --no-cache-dir --retries 10 -r requirements-cloud.txt

# Copy project code
COPY . .

# Create data directories
RUN mkdir -p data/photos data/db

# Expose port
EXPOSE 8000

# Start backend server
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
