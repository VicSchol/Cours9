# tests/conftest.py
import sys
from unittest.mock import MagicMock

# ------------------------------
# Mock FAISS
# ------------------------------
mock_faiss = MagicMock()
mock_faiss.read_index.return_value = MagicMock()
sys.modules["faiss"] = mock_faiss
sys.modules["faiss.swigfaiss"] = MagicMock()
sys.modules["faiss.swigfaiss_avx2"] = MagicMock()
sys.modules["faiss.swigfaiss_avx512"] = MagicMock()

# ------------------------------
# Mock SentenceTransformer
# ------------------------------
mock_st = MagicMock()
mock_model = MagicMock()
mock_model.encode.return_value = [0.1] * 384
mock_st.SentenceTransformer.return_value = mock_model
sys.modules["sentence_transformers"] = mock_st

# ------------------------------
# Mock Torch (évite EasyOCR, warnings, CUDA checks)
# ------------------------------
mock_torch = MagicMock()
mock_torch.cuda.is_available.return_value = False
mock_torch.device.return_value = "cpu"
mock_torch.quantization = MagicMock()
sys.modules["torch"] = mock_torch

# ------------------------------
# Mock EasyOCR (évite le chargement modèle)
# ------------------------------
mock_easyocr = MagicMock()
mock_reader = MagicMock()
mock_reader.readtext.return_value = [["fake text", 0.99]]
mock_easyocr.Reader.return_value = mock_reader
sys.modules["easyocr"] = mock_easyocr

# ------------------------------
# Mock ton module chatbot
# ------------------------------
mock_chatbot = MagicMock()
mock_chatbot.chatbot_ask.return_value = ("Réponse mock", [])
mock_chatbot.index = MagicMock()
mock_chatbot.metadatas = []
sys.modules["chatbot"] = mock_chatbot

# ------------------------------
# Mock ton module vectorisation si nécessaire
# ------------------------------
mock_vect = MagicMock()
mock_vect.load_model.return_value = "mock_model"
mock_vect.vectorise_text.return_value = [0.2] * 384
mock_vect.ocr_image.return_value = "fake ocr"
sys.modules["vectorisation"] = mock_vect
