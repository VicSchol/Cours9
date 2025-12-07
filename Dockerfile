# 🏗️ STAGE 1: THE BUILDER (Installs all heavy dependencies)
FROM python:3.11-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies needed for building packages (e.g., tesseract, numpy)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libtesseract-dev \
    tesseract-ocr \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and prepare requirements.txt
COPY requirements.txt .
RUN sed -i '/pywin32/d' requirements.txt

# INSTALL PYTHON DEPENDENCIES
# This is where the heavy space usage occurs. It runs in the 'builder' stage.
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt


# 🚀 STAGE 2: THE FINAL RUNTIME IMAGE (The one that will be deployed)
FROM python:3.11-slim

# Install ONLY the necessary system dependencies for running the application
RUN apt-get update && apt-get install -y --no-install-recommends \
    libtesseract-dev \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy the installed Python packages from the 'builder' stage
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .

# Final command
CMD ["python", "api/main.py"]