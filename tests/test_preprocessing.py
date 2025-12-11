# tests/test_preprocessing.py
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
import pandas as pd
from unittest.mock import patch
from datetime import datetime, timedelta, timezone
import logging

import src.preprocessing as prep

# ---------------- CONFIGURATION DU LOGGER ---------------- #
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------- FIXTURE SAMPLE DATAFRAME ---------------- #
@pytest.fixture
def sample_raw_df():
    """DataFrame simulant des événements pour les tests."""
    return pd.DataFrame({
        "uid": ["EV1", "EV2"],
        "title_fr": ["Super événement", "Autre événement"],
        "description_fr": ["Desc 1", "Desc 2"],
        "longdescription_fr": ["Long Desc 1", "Long Desc 2"],
        "date_start": [datetime.now().isoformat(), (datetime.now() - timedelta(days=400)).isoformat()],
        "firstdate_begin": [datetime.now().isoformat(), (datetime.now() - timedelta(days=400)).isoformat()],
        "firstdate_end": [datetime.now().isoformat(), (datetime.now() - timedelta(days=400)).isoformat()],
        "lastdate_begin": [datetime.now().isoformat(), (datetime.now() - timedelta(days=400)).isoformat()],
        "lastdate_end": [datetime.now().isoformat(), (datetime.now() - timedelta(days=400)).isoformat()],
        "timings": ["18:00", "20:00"],
        "location_coordinates": ["45.7500,4.8500", "45.7600,4.8600"],
        "image": ["http://fake.url/image1.png", "http://fake.url/image2.png"],
        "age_min": [10, 5],
        "age_max": [99, 12]
    })

# ---------------- TEST RENAME ---------------- #
def test_column_renaming(sample_raw_df):
    logger.info("Test de renommage des colonnes démarré")
    df = sample_raw_df.rename(columns={
        "uid": "event_id",
        "title_fr": "title",
        "description_fr": "description",
        "longdescription_fr": "long_description",
        "date_start": "start_date"
    })
    assert "event_id" in df.columns
    assert "title" in df.columns
    assert "description" in df.columns
    assert "long_description" in df.columns
    assert "start_date" in df.columns
    logger.info("Renommage des colonnes OK")

# ---------------- TEST DATES ---------------- #
def test_date_conversion(sample_raw_df):
    logger.info("Test de conversion des dates démarré")
    df = sample_raw_df.copy()
    df["firstdate_begin"] = pd.to_datetime(df["firstdate_begin"])
    assert isinstance(df["firstdate_begin"].iloc[0], pd.Timestamp)
    logger.info("Conversion des dates OK: %s", df["firstdate_begin"].iloc[0])

def test_filter_last_year(sample_raw_df):
    logger.info("Test de filtrage des événements de l'année dernière démarré")
    df = sample_raw_df.copy()
    df["firstdate_begin"] = pd.to_datetime(df["firstdate_begin"], utc=True)
    one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)
    filtered = df[df["firstdate_begin"] >= one_year_ago]
    logger.info("Nombre d'événements filtrés: %d", len(filtered))
    assert len(filtered) == 1
    assert filtered.iloc[0]["uid"] == "EV1"

# ---------------- TEST BUILD DATES ---------------- #
def test_dates_text(sample_raw_df):
    logger.info("Test de génération des textes de dates démarré")
    df = sample_raw_df.copy()
    df["firstdate_begin"] = pd.to_datetime(df["firstdate_begin"])
    df["firstdate_end"] = pd.to_datetime(df["firstdate_end"])
    df["lastdate_begin"] = pd.to_datetime(df["lastdate_begin"])
    df["lastdate_end"] = pd.to_datetime(df["lastdate_end"])
    text = prep.build_dates(df.iloc[0])
    logger.info("Texte dates généré: %s", text)
    assert "Première date" in text
    assert "Dernière date" in text
    assert "Fin première période" in text

# ---------------- TEST COORDONNEES ---------------- #
def test_coordinate_split(sample_raw_df):
    logger.info("Test de split des coordonnées démarré")
    df = sample_raw_df.copy()
    lat, lon = prep.split_coords(df["location_coordinates"].iloc[0])
    logger.info("Coordonnées extraites: lat=%s, lon=%s", lat, lon)
    assert lat == 45.7500
    assert lon == 4.8500

# ---------------- TEST OCR MOCK ---------------- #
from unittest.mock import patch, MagicMock

@patch("src.preprocessing.easyocr.Reader")
def test_ocr_mock(mock_easyocr_reader, sample_raw_df):
    logger.info("Test OCR démarré (mock)")

    # Mock du reader pour qu'il retourne "Texte OCR"
    mock_reader_instance = MagicMock()
    mock_reader_instance.readtext.return_value = ["Texte OCR"]
    mock_easyocr_reader.return_value = mock_reader_instance

    # Assurer qu'on a une "image" factice
    df = sample_raw_df.copy()
    df["image"].iloc[0] = "fake_url"

    text = prep.ocr_image(df["image"].iloc[0])
    logger.info("Résultat OCR mock: %s", text)

    assert text == "Texte OCR"


# ---------------- TEST VECTORIZATION TEXT ---------------- #
def test_vectorisation_field(sample_raw_df):
    logger.info("Test vectorisation des textes démarré")
    df = sample_raw_df.rename(columns={
        "uid": "event_id",
        "title_fr": "title",
        "description_fr": "description",
        "longdescription_fr": "long_description",
        "date_start": "start_date"
    })
    
    for col in df.columns:
        df[col] = df[col].apply(prep.convert_to_text)

    df["ocr_text"] = "image text"
    df["dates_text"] = "01/05/2024"
    df["geo_text"] = "Coordonnées : 45, 4"
    df["age_text"] = "Âge : 10"

    df["vectorise_text"] = df[["title", "description", "long_description", "ocr_text", "dates_text", "geo_text", "age_text"]].agg(" ".join, axis=1)

    logger.info("Texte vectorisé exemple: %s", df["vectorise_text"].iloc[0])

    assert "Super événement" in df["vectorise_text"].iloc[0]
    assert "image text" in df["vectorise_text"].iloc[0]
