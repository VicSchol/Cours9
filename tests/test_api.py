import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import logging
from api.main import app  # adapte selon ton chemin réel

# ---------------- CONFIGURATION DU LOGGER ---------------- #
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

client = TestClient(app)


# -----------------------------
# TEST /ask
# -----------------------------
@patch("api.main.chatbot_ask")
def test_ask_success(mock_chatbot):
    logger.info("Test /ask success démarré")
    mock_chatbot.return_value = "Réponse simulée"

    payload = {"question": "Quels événements ont lieu aujourd’hui ?"}
    response = client.post("/ask", json=payload)

    logger.info("Réponse reçue: %s", response.json())

    assert response.status_code == 200
    assert response.json()["response"] == "Réponse simulée"
    mock_chatbot.assert_called_once_with(payload["question"])
    logger.info("Test /ask success terminé")


def test_ask_empty_question():
    logger.info("Test /ask question vide démarré")
    response = client.post("/ask", json={"question": ""})

    logger.info("Réponse reçue: %s", response.json())
    assert response.status_code == 400
    assert "ne peut pas être vide" in response.json()["detail"]
    logger.info("Test /ask question vide terminé")


@patch("api.main.chatbot_ask", side_effect=Exception("Erreur interne"))
def test_ask_internal_error(mock_chatbot):
    logger.info("Test /ask internal error démarré")
    response = client.post("/ask", json={"question": "Test"})

    logger.info("Réponse reçue: %s", response.json())
    assert response.status_code == 500
    assert response.json()["detail"] == "Erreur interne"
    logger.info("Test /ask internal error terminé")


# -----------------------------
# TEST /rebuild
# -----------------------------
@patch("api.main.faiss.read_index")
@patch("api.main.pickle.load")
def test_rebuild_success(mock_pickle, mock_faiss):
    logger.info("Test /rebuild success démarré")
    mock_faiss.return_value = MagicMock()
    mock_pickle.return_value = [{"id": 1}]

    response = client.get("/rebuild")
    logger.info("Réponse reçue: %s", response.json())

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    mock_faiss.assert_called_once()
    mock_pickle.assert_called_once()
    logger.info("Test /rebuild success terminé")


@patch("api.main.faiss.read_index", side_effect=Exception("FAISS cassé"))
def test_rebuild_failure(mock_faiss):
    logger.info("Test /rebuild failure démarré")
    response = client.get("/rebuild")
    logger.info("Réponse reçue: %s", response.json())

    assert response.status_code == 500
    assert response.json()["detail"] == "FAISS cassé"
    logger.info("Test /rebuild failure terminé")
