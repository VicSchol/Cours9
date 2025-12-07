# Stage 1: The Builder Stage
# 1️⃣ Image Python légère
FROM python:3.11-slim AS builder

# 2️⃣ Variables d'environnement Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3️⃣ Installer les dépendances système nécessaires
# Keep this step as it's needed to build packages like tesseract
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libtesseract-dev \
    tesseract-ocr \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

# 4️⃣ Créer le dossier de travail
WORKDIR /app

# 5️⃣ Copier et modifier requirements.txt
COPY requirements.txt .
RUN sed -i '/pywin32/d' requirements.txt

# 7️⃣ Installer les dépendances Python in the builder
# Note: --no-cache-dir is already good practice
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# --- Start of Final Stage ---
# 8️⃣ Final (Smaller) Runtime Image
FROM python:3.11-slim

# 9️⃣ Re-install only the runtime system dependencies
# This is usually only needed for the libraries that rely on system libs (like tesseract)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libtesseract-dev \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# 🔟 Copy application files and installed packages from the builder stage
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .

# 11 Copy the source files
COPY requirements.txt .

# 12 Default command
CMD ["python", "api/main.py"]