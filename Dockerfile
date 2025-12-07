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

# 5️⃣ Copier le fichier requirements.txt
COPY requirements.txt .

# 6️⃣ Modifier requirements.txt pour ignorer pywin32
#    (Si ton requirements.txt contient "pywin32==311", remplace par :)
#    pywin32==311 ; sys_platform == "win32"
RUN sed -i '/pywin32/d' requirements.txt

# 7️⃣ Installer les dépendances Python
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 8️⃣ Copier le reste du projet
COPY . .

# 9️⃣ Commande par défaut
CMD ["python", "api/main.py"]
