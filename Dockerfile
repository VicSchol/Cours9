# 1️⃣ Image Python légère
FROM python:3.11-slim

# 2️⃣ Variables d'environnement Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3️⃣ Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libtesseract-dev \
    tesseract-ocr \
    pkg-config \
    git \
    && rm -rf /var/lib/apt/lists/*

# 4️⃣ Créer le dossier de travail
WORKDIR /app

# 5️⃣ Copier uniquement le fichier requirements pour profiter du cache Docker
COPY requirements.txt /app/

# 6️⃣ Installer les dépendances Python
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 7️⃣ Copier le reste du projet
COPY . /app

# 8️⃣ Commande par défaut
CMD ["python", "api/main.py"]
