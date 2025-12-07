# %% --------------------------- IMPORTS ---------------------------
import pandas as pd
from sentence_transformers import SentenceTransformer

# %% --------------------------- 1. CONFIG ---------------------------
INPUT_FILENAME = "src/evenements_lyon_prets.feather"
OUTPUT_FILENAME_VECTOR = "src/evenements_lyon_vectorises.jsonl"
MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 64

# %% --------------------------- 2. CHARGEMENT DU DATAFRAME ---------------------------
try:
    df = pd.read_feather(INPUT_FILENAME)
    print(f"✅ DataFrame chargé : {INPUT_FILENAME}")
    print(f"Nombre d'événements : {len(df)}")
except Exception as e:
    print(f"⚠️ Erreur chargement : {e}")
    exit()


import re
from bs4 import BeautifulSoup

def clean_text(text):
    """
    Nettoie un texte HTML / riche pour le rendre exploitable pour la vectorisation.
    - Supprime balises HTML (<p>, <ul>, <li>, etc.)
    - Supprime caractères spéciaux indésirables
    - Supprime espaces multiples
    """
    if not text:
        return ""

    # 1. Supprimer le HTML via BeautifulSoup
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(separator=" ")  # garde un espace entre les blocs

    # 2. Supprimer caractères spéciaux inutiles
    text = re.sub(r"[\r\n\t]", " ", text)  # retour chariot, tab
    text = re.sub(r"\s+", " ", text)       # multiples espaces → 1 espace
    text = text.strip()

    return text


df['vectorise_text'] = df['vectorise_text'].apply(clean_text)
# %% --------------------------- 2b. EXPLORATION DU DATAFRAME ---------------------------
print("\n--- Types et informations des colonnes ---")
print(df.dtypes)
print("\n--- Informations complètes du DataFrame ---")
print(df.info())
print("\n--- Aperçu des premières lignes ---")
print(df.head())

# Vérification de la colonne à vectoriser
if "vectorise_text" not in df.columns:
    raise ValueError("La colonne 'vectorise_text' est manquante. Impossible de vectoriser.")

# %% --------------------------- 3. INITIALISATION DU MODELE ---------------------------
print(f"\nChargement du modèle d'embedding : {MODEL_NAME}...")
model = SentenceTransformer(MODEL_NAME)
print("✅ Modèle chargé.")

# %% --------------------------- 4. VECTORISATION ---------------------------
texts = df["vectorise_text"].tolist()
print(f"\nVectorisation de {len(texts)} textes...")

embeddings = model.encode(
    texts,
    batch_size=BATCH_SIZE,
    show_progress_bar=True,
    normalize_embeddings=True
)

# Ajout des embeddings au DataFrame
df["embedding"] = [vec.tolist() for vec in embeddings]
print("✅ Vectorisation terminée.")

# %% --------------------------- 5. ENREGISTREMENT ---------------------------
try:
    df.to_json(
        OUTPUT_FILENAME_VECTOR,
        orient="records",
        lines=True,
        force_ascii=False  # conserver les accents
    )
    print(f"✅ DataFrame vectorisé sauvegardé : {OUTPUT_FILENAME_VECTOR}")
except Exception as e:
    print(f"⚠️ Erreur sauvegarde : {e}")
