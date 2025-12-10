# -------------------------------
# STAGE 1: BUILDER
# -------------------------------
FROM python:3.11-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libtesseract-dev \
    tesseract-ocr \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Clean requirements
COPY requirements.txt . 
RUN sed -i '/pywin32/d' requirements.txt

# Install CPU torch
RUN pip install --upgrade pip \
    && pip install --no-cache-dir torch==2.2.2+cpu torchvision==0.17.2+cpu \
       --extra-index-url https://download.pytorch.org/whl/cpu

# Install remaining deps
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------
# Build index vectoriel pendant le build
# -------------------------------
COPY . .
RUN python scripts/build_all.py

# -------------------------------
# STAGE 2: FINAL IMAGE
# -------------------------------
FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    libtesseract-dev \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copie les packages Python
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copie le projet et l’index FAISS généré
COPY --from=builder /app /app

EXPOSE 8080

# Lancement de l’API
CMD ["python", "api/main.py"]
