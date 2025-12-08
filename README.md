# 🚀 Projet O.C. : Reconnaissance de Texte (OCR) et Traitement de Langage (LLM)

Ce projet, réalisé dans le cadre du Cours 9 de la formation Data Scientist OpenClassRoom, vise à déployer une API Fastapi capable d'effectuer de l'**OCR** (Optical Character Recognition) sur des documents d'entrée, puis d'utiliser des modèles de **LLM/LangChain** pour extraire et structurer l'information. 
Un Chatbot est capable de répondre à des utilisateurs posant
des questions à propos d'évènements ayant lieu dans la ville de Lyon


## 🎯 Objectifs du Projet

* **Extraction de Données:** Utiliser `easyocr` ou `pytesseract` pour convertir le texte des images/PDFs.
* **Traitement de l'Information:** Utiliser les bibliothèques `langchain` et `sentence-transformers` pour l'analyse, l'indexation et la réponse aux questions (RAG - Retrieval Augmented Generation).
* **Conteneurisation:** Déployer l'application sous forme de service web (`FastAPI` + `Uvicorn`) via **Docker**.

---

## 🏗️ Architecture du Projet


Le projet suit une structure modulaire :

| Dossier/Fichier | Description |
| :--- | :--- |
| `api/` | Contient le code principal de l'API (`main.py`, points d'accès Fastapi). |
| `src/` | Contient la logique métier, les classes de modèles, et les fonctions de traitement OCR/Langchain. |
| `db/` | (Probablement) Contient les fichiers de base de données, les index Faiss ou les modèles sauvegardés. |
| `tests/` | Contient les tests unitaires et d'intégration (avec `pytest`). |
| `requirements.txt` | Liste de toutes les dépendances Python nécessaires (incluant Torch, Transformers, LangChain, etc.). |
| `Dockerfile` | Instructions pour construire l'image Docker de l'application. |

---

## Pipeline RAG – Diagramme Mermaid

```mermaid
flowchart LR
    A[Base de données<br>Source : événements à Lyon] --> B[Transfo en texte exploitable<br>(OCR / conversion en texte)]
    B --> C[Embeddings]
    C --> D[Chunking]
    D --> E[Vectorisation]
    E --> F[DB avec indexation Faiss]
    F --> G[RAG, recherche par similarité vectorielle]
    G --> H[Réponse structurée (Mistral V1)]

---

## ⚙️ Démarrage Local (sans Docker)

### Prérequis

* Python 3.11
* Un environnement virtuel (`venv`)

### Étapes

1.  **Cloner le dépôt:**
    ```bash
    git clone [LIEN_DU_DEPOT_GIT]
    cd [NOM_DU_REPERTOIRE]
    ```

2.  **Créer et activer l'environnement virtuel:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate  # Sous Windows
    # source venv/bin/activate # Sous Linux/macOS
    ```

3.  **Installer les dépendances:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Lancer l'API:**
    ```bash
    uvicorn api.main:app --reload
    ```
    L'API sera accessible à l'adresse `http://127.0.0.1:8000`. La documentation Swagger (OpenAPI) est disponible sur `http://127.0.0.1:8000/docs`.

---

## 🐳 Déploiement avec Docker (Recommandé)

### Prérequis

* Docker Desktop installé et démarré.

### 1. Construction de l'image

La construction peut prendre du temps en raison de la taille des dépendances (`torch`, `transformers`).

```bash
docker build -t ocr-llm-api:latest .

