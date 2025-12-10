import sys
from unittest.mock import MagicMock

# Empêche l'import réel de FAISS
sys.modules["faiss"] = MagicMock()