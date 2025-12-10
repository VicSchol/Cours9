import subprocess
import sys

PY = sys.executable  # ← utilise automatiquement le python du venv

print("🚀 Running preprocessing...")
subprocess.check_call([PY, "src/preprocessing.py"])

print("🧠 Running vectorisation...")
subprocess.check_call([PY, "src/vectorisation.py"])

print("📚 Building FAISS index...")
subprocess.check_call([PY, "db/vectorial_db.py"])

print("🎉 All steps completed!")
