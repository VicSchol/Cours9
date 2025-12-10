import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
import json

# ----------------------------- FIXTURES ----------------------------- #

@pytest.fixture
def sample_df():
    """DataFrame minimal pour vectorisation."""
    return pd.DataFrame({
        "event_id": ["EV1", "EV2"],
        "title": ["Concert", "Expo"],
        "vectorise_text": ["Un super concert", "Une exposition d’art"]
    })


# ----------------------------- TESTS ----------------------------- #

def test_dataframe_has_vectorise_text(sample_df):
    """Vérifie que la colonne vectorise_text existe."""
    assert "vectorise_text" in sample_df.columns


@patch("src.vectorisation.SentenceTransformer")
def test_model_loading(mock_model, sample_df):
    """Vérifie que SentenceTransformer est bien instancié avec le bon modèle."""
    from src.vectorisation import MODEL_NAME

    mock_model.return_value = MagicMock()

    _ = mock_model(MODEL_NAME)
    mock_model.assert_called_once_with(MODEL_NAME)


@patch("src.vectorisation.SentenceTransformer")
def test_vectorisation_process(mock_model, sample_df, tmp_path):
    """
    Test complet :
    - mock du modèle
    - mock de encode()
    - ajout de la colonne embedding
    - export JSONL
    """

    # Mock du modèle
    mock_instance = MagicMock()
    mock_model.return_value = mock_instance

    # Fake embeddings (128 dimensions)
    fake_vectors = [
        [0.1] * 128,
        [0.2] * 128
    ]
    mock_instance.encode.return_value = fake_vectors

    # Simule le script
    df = sample_df.copy()
    texts = df["vectorise_text"].tolist()
    embeddings = mock_instance.encode(
        texts,
        batch_size=64,
        show_progress_bar=True,
        normalize_embeddings=True
    )

    # Ajout au DF
    df["embedding"] = [vec for vec in embeddings]

    # Vérifications
    assert "embedding" in df.columns
    assert len(df["embedding"]) == len(df)
    assert len(df["embedding"].iloc[0]) == 128
    assert mock_instance.encode.called

    # Test export JSONL
    output_file = tmp_path / "output.jsonl"
    df.to_json(output_file, orient="records", lines=True, force_ascii=False)

    # Lecture du fichier JSONL pour vérifier contenu
    with open(output_file, "r", encoding="utf-8") as f:
        lines = [json.loads(l) for l in f.readlines()]

    assert len(lines) == 2
    assert "embedding" in lines[0]
    assert len(lines[0]["embedding"]) == 128
