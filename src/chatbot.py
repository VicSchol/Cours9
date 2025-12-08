# %% src/chatbot.py
import os, sys
import pickle
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from datetime import datetime
import re
import requests
from dotenv import load_dotenv

# Charge les variables d'environnement depuis le fichier .env
load_dotenv()

# --------------------------- CONFIG ---------------------------
BASE_DIR = os.path.dirname(__file__)

INDEX_FILE = Path(__file__).resolve().parent.parent / "db" / "faiss_evenements.index"
METADATAS_FILE = Path(__file__).resolve().parent.parent / "db" / "metadatas.pkl"
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K = 5  # nombre de chunks à récupérer

# --------------------------- WRAPPER MISTRAL ---------------------------
class MistralLLM:
    def __init__(self, api_key, model_name="mistral-small-latest"):
        self.api_key = api_key
        self.model_name = model_name
        self.api_url = "https://api.mistral.ai/v1/chat/completions"

    def __call__(self, prompt, temperature=0.7, max_tokens=512):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        response = requests.post(self.api_url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]

# --------------------------- CHARGEMENT DE L'INDEX ET MÉTADONNÉES ---------------------------
print("Chargement de l'index Faiss et des métadonnées...")
index = faiss.read_index(str(INDEX_FILE))
with open(METADATAS_FILE, "rb") as f:
    metadatas = pickle.load(f)

# --------------------------- CHARGEMENT DU MODEL D'EMBEDDING ---------------------------
model = SentenceTransformer(EMBEDDING_MODEL_NAME)

# Remplace par ta clé API Mistral
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "YOUR_API_KEY")
print("MISTRAL_API_KEY =", MISTRAL_API_KEY)

llm = MistralLLM(api_key=MISTRAL_API_KEY)

# --------------------------- FILTRAGE DES ÉVÉNEMENTS DU JOUR ---------------------------
def filter_events_today(events):
    today = datetime.now().date()
    filtered = []
    for e in events:
        dates_text = e.get("dates_text", "")
        matches = re.findall(r"\d{2}/\d{2}/\d{4}", dates_text)
        for m in matches:
            try:
                d = datetime.strptime(m, "%d/%m/%Y").date()
                if d == today:
                    filtered.append(e)
                    break
            except:
                continue
    return filtered if filtered else events

# --------------------------- FONCTION CHATBOT ---------------------------
last_event = None  # variable globale pour références vagues

def chatbot_ask(question, top_k=TOP_K):
    global last_event

    # 1. Obtenir la date d'aujourd'hui
    today_date = datetime.now()
    today_str = today_date.strftime("%d %B %Y")  # ex: 05 Décembre 2025
    current_month_name = today_date.strftime("%B")
    current_year = today_date.strftime("%Y")

    # Détection des références vagues
    vague_refs = ["cet événement", "cet atelier", "cette activité", "plus de détails"]

    # 2. Recherche vectorielle
    if any(ref in question.lower() for ref in vague_refs) and last_event:
        retrieved_chunks = [last_event]
    else:
        q_vec = model.encode(question, normalize_embeddings=True).astype('float32')
        D, I = index.search(np.array([q_vec]), top_k)
        retrieved_chunks = [metadatas[i] for i in I[0]]

    # Mise à jour du dernier événement
    if retrieved_chunks:
        last_event = retrieved_chunks[0]

    # 3. Construire le prompt
    prompt = "Tu es un assistant sympathique et humain spécialisé dans les événements de Lyon.\n"
    prompt += f"La date d'aujourd'hui est le **{today_str}**.\n"
    prompt += f"Le mois actuel est **{current_month_name} {current_year}**.\n"
    prompt += "Ta mission est de répondre à la question de l'utilisateur en français en utilisant UNIQUEMENT les informations ci-dessous.\n"
    prompt += "Voici les événements pertinents récupérés par la recherche vectorielle :\n"

    context_texts = []
    for m in retrieved_chunks:
        title = m.get("title", "Titre inconnu")
        dates = m.get("dates_text", "dates inconnues")
        geo = m.get("geo_text", "lieu inconnu")
        vector_text = m.get("vectorise_text", "")
        prompt += f"- **{title}** ({dates}, {geo}). Description : {vector_text}\n"

        # On construit context_texts avec plusieurs champs pour plus de chance de récupérer du texte
        full_text = m.get("full_vectorise_text") or m.get("vectorise_text") or m.get("context_chunk") or ""
        if full_text.strip():
            context_texts.append(full_text.strip())

    # Si aucun contexte trouvé, ajouter au moins le titre + dates pour ne pas renvoyer vide
    if not context_texts:
        for m in retrieved_chunks:
            context_texts.append(f"{m.get('title', 'Titre inconnu')} ({m.get('dates_text', 'dates inconnues')})")

    prompt += f"\nQuestion de l'utilisateur : {question}\nRéponse :"

    # 4. Appel à Mistral
    response = llm(prompt)

    # 5. Affichage des sources utilisées
    print("\n--- Sources utilisées ---")
    for text in context_texts:
        print(f"- {text[:150]}{'...' if len(text) > 150 else ''}")

    return response, context_texts


# --------------------------- INTERACTION ---------------------------
if __name__ == "__main__":
    print("Chatbot prêt ! Posez vos questions sur les événements de Lyon.")
    while True:
        user_input = input("\nVous : ")
        if user_input.lower() in ["quit", "exit"]:
            print("Au revoir !")
            break
        response = chatbot_ask(user_input)
        print("\nChatbot : ", response)
