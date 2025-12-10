import os, sys
import json
import pandas as pd
from datasets import Dataset
import nest_asyncio
import traceback
from langchain_mistralai.chat_models import ChatMistralAI
from langchain_mistralai.embeddings import MistralAIEmbeddings
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from pathlib import Path

# ----------------- CHEMINS ----------------- #
BASE_DIR = Path(__file__).resolve().parent.parent
SRC_DIR = BASE_DIR / "src"
sys.path.insert(0, str(SRC_DIR))


from chatbot import chatbot_ask  # ton chatbot

nest_asyncio.apply()

# ----------------- CONFIG ----------------- #
TEST_FILE = Path(__file__).parent / "rag_ground_truth.json"  # Chemin vers ton fichier JSON
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "VOTRE_CLE_API_MISTRAL_ICI")

if MISTRAL_API_KEY == "VOTRE_CLE_API_MISTRAL_ICI" or not MISTRAL_API_KEY:
    print("⚠️ AVERTISSEMENT : Clé API Mistral non trouvée ou non définie.")

# ----------------- CHARGEMENT DES EXEMPLES ----------------- #
with open(TEST_FILE, "r", encoding="utf-8") as f:
    examples = json.load(f)

questions_test = [ex["question"] for ex in examples]
ground_truths = [ex["ground_truth_answer"] for ex in examples]
placeholder_contexts = [ex["ground_truth_context"] for ex in examples]

# Générer les réponses et récupérer le contexte utilisé par le chatbot
answers = []
retrieved_contexts = []
for q in questions_test:
    ans, ctx = chatbot_ask(q)
    answers.append(ans)
    retrieved_contexts.append(ctx)

# ----------------- PREPARATION DATASET RAGAS ----------------- #
evaluation_data = {
    "question": questions_test,
    "answer": answers,
    "contexts": retrieved_contexts,
    "ground_truth": ground_truths
}
evaluation_dataset = Dataset.from_dict(evaluation_data)
print("Dataset d'évaluation prêt.")

# ----------------- INITIALISATION LLM ET EMBEDDINGS ----------------- #
try:
    mistral_llm = ChatMistralAI(
        mistral_api_key=MISTRAL_API_KEY,
        model="mistral-small-latest",
        temperature=0.1
    )
    mistral_embeddings = MistralAIEmbeddings(mistral_api_key=MISTRAL_API_KEY)
    print("LLM et Embeddings initialisés.")

    # ----------------- METRICS ----------------- #
    metrics_to_evaluate = [
        faithfulness,
        answer_relevancy,
        context_precision,
        context_recall,
    ]
    print(f"Métriques sélectionnées: {[m.name for m in metrics_to_evaluate]}")

    # ----------------- EVALUATION ----------------- #
    print("\nLancement de l'évaluation Ragas (peut prendre du temps)...")
    results = evaluate(
        dataset=evaluation_dataset,
        metrics=metrics_to_evaluate,
        llm=mistral_llm,
        embeddings=mistral_embeddings
    )
    print("\n--- Évaluation Ragas terminée ---")

    # ----------------- AFFICHAGE DES RESULTATS ----------------- #
    results_df = results.to_pandas()
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    pd.set_option('display.max_colwidth', 150)
    print(results_df)

    # ----------------- SCORES MOYENS ----------------- #
    print("\n--- Scores Moyens (sur tout le dataset) ---")
    average_scores = results_df.mean(numeric_only=True)
    print(average_scores)

except Exception as e:
    print(f"\n❌ ERREUR lors de l'initialisation ou de l'évaluation Ragas : {e}")
    traceback.print_exc()
