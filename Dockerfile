# -------------------------------
# STAGE 1: BUILDER
# -------------------------------
FROM python:3.11-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Installer les dépendances système nécessaires pour Torch, FAISS, OCR, Tesseract
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libtesseract-dev \
    tesseract-ocr \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier requirements et nettoyer si besoin
COPY requirements.txt .
RUN sed -i '/pywin32/d' requirements.txt

# Installer Torch CPU
RUN pip install --upgrade pip \
    && pip install --no-cache-dir torch==2.2.2+cpu torchvision==0.17.2+cpu \
       --extra-index-url https://download.pytorch.org/whl/cpu

# Installer le reste des dépendances
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------
# Build index vectoriel pendant le build
# -------------------------------
# Copier le projet entier
COPY . .

# Exécuter le script qui construit preprocessing, vectorisation et FAISS
RUN python scripts/build_all.py

# -------------------------------
# STAGE 2: FINAL IMAGE
# -------------------------------
FROM python:3.11-slim

# Installer Tesseract runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    libtesseract-dev \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copier les packages Python depuis le builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

# Copier tout le projet + index FAISS déjà construit
COPY --from=builder /app /app

EXPOSE 8080

# Lancer l’API
CMD ["python", "api/main.py"]
