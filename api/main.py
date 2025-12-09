import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
import faiss
import pickle
import logging
import subprocess
import time
import webbrowser
from threading import Thread

# --------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "src"))

from chatbot import chatbot_ask, index, metadatas  # Import du chatbot existant

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="API Chatbot Événements Lyon",
    description="API pour interroger un chatbot basé sur FAISS et des événements à Lyon",
    version="1.0.0"
)

INDEX_FILE = BASE_DIR / "db/faiss_evenements.index"
METADATAS_FILE = BASE_DIR / "db/metadatas.pkl"

# --------------------------------------------------------------------
# Variables globales
# --------------------------------------------------------------------
last_ask_metadata = []  # stocke les métadatas utilisées par la dernière question

# --------------------------------------------------------------------
# Modèle de requête
# --------------------------------------------------------------------
class QuestionRequest(BaseModel):
    question: str = Field(
        ...,
        example="Quels événements ce week-end à Lyon ?",
        description="La question envoyée au chatbot"
    )

# --------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------
@app.get("/health", tags=["Système"])
async def health():
    """Vérifie que l'API fonctionne."""
    return {"status": "ok"}

@app.post("/ask", tags=["Chatbot"])
async def ask_question(request: QuestionRequest):
    """Pose une question au chatbot."""
    global last_ask_metadata
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide.")
    try:
        response_text, response_metadata = chatbot_ask(question)
        last_ask_metadata = response_metadata  # Mise à jour des métadatas de la dernière requête
        return {
            "question": question,
            "response": response_text,
            "metadata": response_metadata
        }
    except Exception as e:
        logger.error(f"Erreur dans /ask : {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/rebuild", tags=["Administration"])
async def rebuild_index():
    """Recharge l'index FAISS et les métadonnées."""
    try:
        global index, metadatas
        if not INDEX_FILE.exists():
            raise FileNotFoundError(f"Index introuvable : {INDEX_FILE}")
        index = faiss.read_index(str(INDEX_FILE))
        with open(METADATAS_FILE, "rb") as f:
            metadatas = pickle.load(f)
        return {"status": "success", "message": "Index et métadonnées rechargés."}
    except Exception as e:
        logger.error(f"Erreur dans /rebuild : {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metadata", tags=["Administration"])
async def get_metadata():
    """Renvoie les métadatas utilisées par la dernière requête /ask."""
    try:
        global last_ask_metadata
        if not last_ask_metadata:
            return {"message": "Aucune question traitée pour le moment.", "metadata": []}
        return {
            "metadata_count": len(last_ask_metadata),
            "metadata_sample": last_ask_metadata
        }
    except Exception as e:
        logger.error(f"Erreur dans /metadata : {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --------------------------------------------------------------------
# Lancement local
# --------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=8080)

    # Démarrer le serveur dans un thread séparé
    server_thread = Thread(target=run_server, daemon=True)
    server_thread.start()

    # Petit délai pour laisser le serveur démarrer
    time.sleep(2)

    # Ouvrir Swagger /docs automatiquement
    swagger_url = "http://127.0.0.1:8080/docs"
    logger.info(f"Ouvrir Swagger automatiquement : {swagger_url}")
    webbrowser.open(swagger_url)
    
    # Exemple de commande curl automatique vers /ask
    curl_command = [
        "curl",
        "-X", "POST",
        "http://127.0.0.1:8080/ask",
        "-H", "Content-Type: application/json",
        "-d", '{"question":"Quels événements ce week-end à Lyon ?"}'
    ]
    logger.info("Test curl vers /ask :")
    subprocess.run(curl_command)

    # Maintenir le serveur actif
    server_thread.join()
