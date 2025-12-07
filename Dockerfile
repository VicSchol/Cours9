# 1. Image Python légère
FROM python:3.11-slim

# 2. Empêcher Python d'écrire les .pyc sur le conteneur
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Installer quelques dépendances système
RUN apt-get update && apt-get install -y \
    build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# 4. Créer un dossier dans le conteneur
WORKDIR /app

# 5. Copier les fichiers du projet
COPY . /app

# 6. Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# 7. Commande par défaut : lancer ton API
CMD ["python", "api/main.py"]
