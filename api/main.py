import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "src"))

from pydantic import BaseModel
from chatbot import chatbot_ask, index, metadatas  # on importe ton chatbot existant
import faiss
import pickle
from pathlib import Path
from fastapi import FastAPI, HTTPException
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Chatbot Événements Lyon")

BASE_DIR = Path(__file__).parent.parent
INDEX_FILE = BASE_DIR / "db/faiss_evenements.index"
METADATAS_FILE = BASE_DIR / "db/metadatas.pkl"

# --------------------------- Modèle de requête ---------------------------
class QuestionRequest(BaseModel):
    question: str

# --------------------------- Endpoint /ask ---------------------------
@app.post("/ask")
async def ask_question(request: QuestionRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide.")
    try:
        response = chatbot_ask(question)  # Appelle ton chatbot directement
        return {"question": question, "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --------------------------- Endpoint /rebuild ---------------------------
@app.get("/rebuild")
async def rebuild_index():
    try:
        global index, metadatas
        index = faiss.read_index(str(INDEX_FILE))
        with open(METADATAS_FILE, "rb") as f:
            metadatas = pickle.load(f)
        return {"status": "success", "message": "Index et métadonnées rechargés."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    logger.info("Démarrage local uvicorn")
    uvicorn.run(app, host="127.0.0.1", port=8080)
# http://localhost:8080/docs#/default/ask_question_ask_post