import sys
from unittest.mock import MagicMock

# Mock FAISS pour GitHub Actions
mock_faiss = MagicMock()
mock_faiss.read_index.return_value = MagicMock()
sys.modules['faiss'] = mock_faiss
sys.modules['faiss.swigfaiss'] = MagicMock()
sys.modules['faiss.swigfaiss_avx2'] = MagicMock()
sys.modules['faiss.swigfaiss_avx512'] = MagicMock()

# Mock SentenceTransformer
mock_st = MagicMock()
mock_model = MagicMock()
mock_model.encode.return_value = [0.1] * 384
mock_st.SentenceTransformer.return_value = mock_model
sys.modules['sentence_transformers'] = mock_st

# Mock chatbot internals
sys.modules['chatbot'] = MagicMock(
    chatbot_ask=lambda q: ("Réponse mock", []),
    index=MagicMock(),
    metadatas=[]
)
