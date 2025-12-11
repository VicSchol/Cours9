# %% --------------------------- IMPORTS ---------------------------
import pandas as pd
import re
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

# %% --------------------------- CONFIG ---------------------------
INPUT_FILENAME = "src/evenements_lyon_prets.feather"
OUTPUT_FILENAME_VECTOR = "src/evenements_lyon_vectorises.jsonl"
MODEL_NAME = "all-MiniLM-L6-v2"
BATCH_SIZE = 64


# %% --------------------------- FUNCTIONS ---------------------------
def clean_text(text):
    """Nettoie un texte HTML pour la vectorisation."""
    if not text:
        return ""

    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text(separator=" ")

    text = re.sub(r"[\r\n\t]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_dataframe(path):
    """Charge le dataframe brut."""
    return pd.read_feather(path)


def preprocess_dataframe(df):
    """Nettoyage des champs pour vectorisation."""
    if "vectorise_text" not in df.columns:
        raise ValueError("La colonne 'vectorise_text' est manquante.")

    df["vectorise_text"] = df["vectorise_text"].apply(clean_text)
    return df


def export_json(df, path):
    """Export JSONL final."""
    df.to_json(
        path,
        orient="records",
        lines=True,
        force_ascii=False
    )


# %% ----------- MAIN SCRIPT: exécuté UNIQUEMENT en ligne de commande -----------

if __name__ == "__main__":
    try:
        df = load_dataframe(INPUT_FILENAME)
        print(f"✅ DataFrame chargé : {INPUT_FILENAME}")
        print(f"Nombre d'événements : {len(df)}")
    except Exception as e:
        print(f"⚠️ Erreur chargement : {e}")
        exit(1)

    df = preprocess_dataframe(df)

    print("\n--- Infos DataFrame ---")
    print(df.info())
    print(df.head())

    try:
        export_json(df, OUTPUT_FILENAME_VECTOR)
        print(f"✅ Json vectorisé sauvegardé : {OUTPUT_FILENAME_VECTOR}")
    except Exception as e:
        print(f"⚠️ Erreur sauvegarde : {e}")
        exit(1)
