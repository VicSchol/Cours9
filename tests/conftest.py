import sys
import types
from unittest.mock import MagicMock

# Créer un module factice faiss qui ressemble à un vrai module
fake_faiss = types.ModuleType("faiss")

# Ajouter les fonctions utilisées dans ton code
fake_faiss.read_index = MagicMock()
fake_faiss.write_index = MagicMock()

# Si ton chatbot utilise faiss.IndexFlatL2 ou d'autres, tu peux rajouter :
fake_faiss.IndexFlatL2 = MagicMock()
fake_faiss.normalize_L2 = MagicMock()

# Remplacer le module faiss réel par le fake
sys.modules["faiss"] = fake_faiss