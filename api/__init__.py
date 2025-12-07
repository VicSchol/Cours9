from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from src.chatbot import chatbot_ask, index, metadatas  # importer le RAG existant
import faiss
import pickle
from pathlib import Path

app = FastAPI(title="API RAG - Chatbot Événements Lyon")

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
        response = chatbot_ask(question)
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
