# %% --------------------------- IMPORTS ---------------------------
from pathlib import Path
import os, sys
import pandas as pd
import json
from io import StringIO
sys.path.append(str(Path(__file__).resolve().parent.parent / "src"))


# %% --------------------------- CONFIGURATION DES CHEMINS ---------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "db"
DB_DIR.mkdir(exist_ok=True)  # crée le dossier si non existant

FAISS_INDEX_FILE = DB_DIR / "faiss_evenements.index"
METADATAS_FILE = DB_DIR / "metadatas.pkl"


input_file = Path(__file__).resolve().parent.parent / "src" / "evenements_lyon_vectorises.jsonl"
# Lecture sûre du JSONL
with open(input_file, "r", encoding="utf-8") as f:
    data = f.read()

df = pd.read_json(StringIO(data), lines=True)

print(f"Nombre d'événements chargés : {len(df)}")
# %% --------------------------- EXTRACTION DES CHUNKS DE TEXTE ---------------------------

def split_text(text, chunk_size=500, chunk_overlap=50):
    """
    Découpe un texte en chunks, mais ne découpe pas si le texte est inférieur 
    à la taille du chunk.
    """
    if not text:
        return []
    
    text_len = len(text)
    
    # NE PAS CHUNKER si le texte est déjà court et dense
    if text_len <= chunk_size:
        return [text]

    chunks = []
    start = 0
    
    while start < text_len:
        end = min(start + chunk_size, text_len)
        chunks.append(text[start:end])
        # Assurez-vous de ne pas avoir de chevauchement négatif à la fin
        start = start + chunk_size - chunk_overlap 
        if start >= text_len:
            break
            
    return chunks

# Appliquer le split à la colonne vectorise_text (code inchangé ici)
df['chunks'] = df['vectorise_text'].apply(lambda x: split_text(x))


# %% --------------------------- VECTORISATION DES CHUNKS ---------------------------
from sentence_transformers import SentenceTransformer
import numpy as np

model = SentenceTransformer("all-MiniLM-L6-v2")

vectors = []
metadatas = []


for _, row in df.iterrows():
    for chunk in row['chunks']:
        vec = model.encode(chunk, normalize_embeddings=True).astype('float32')
        vectors.append(vec)
        # Capture toutes les infos du texte vectorisé
        metadatas.append({
            "event_id": row.get("event_id", ""),
            "title": row.get("title", ""),
            "dates_text": row.get("dates_text", ""),
            "geo_text": row.get("geo_text", ""),
            "vectorise_text": row.get("vectorise_text", ""),  # toutes les infos
            "chunk": chunk
        })

vectors = np.array(vectors, dtype='float32')
# %% --------------------------- CRÉATION DE L'INDEX FAISS ---------------------------
import faiss

d = vectors.shape[1]  # dimension des embeddings
index = faiss.IndexFlatIP(d)  # Index pour similarité cosinus (normalisé)
index.add(vectors)

print(f"Index Faiss créé avec {index.ntotal} vecteurs")

# Sauvegarde dans le dossier db
faiss.write_index(index, str(FAISS_INDEX_FILE))
print(f"Index FAISS sauvegardé dans {FAISS_INDEX_FILE}")

# %% --------------------------- SAUVEGARDE DES MÉTADONNÉES ---------------------------
import pickle

with open(METADATAS_FILE, "wb") as f:
    pickle.dump(metadatas, f)
print(f"Métadonnées sauvegardées dans {METADATAS_FILE}")

# %% --------------------------- EXEMPLE DE RECHERCHE ---------------------------
query = "Concert de jazz à Paris cet été"
q_vec = model.encode(query, normalize_embeddings=True).astype('float32')

k = 5  # nombre de résultats
D, I = index.search(np.array([q_vec]), k)

print("Résultats les plus proches :")
for i in I[0]:
    print(metadatas[i]['title'], "-", metadatas[i]['dates_text'], "-", metadatas[i]['geo_text'])

# %%
