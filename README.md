# 📌 Dataverse Agent – CRM Intelligent

Agent Python connecté à Microsoft Dataverse permettant :
- Extraction & lecture automatique des entités
- Génération de plans de requêtes OData via LLM
- Synthèse de réponses basée sur le contexte
- Support API FastAPI + intégration LLM (Gemini)

---

##  Fonctionnalités principales

| Fonction | Description |
|---|---|
|  Query Planner LLM | Analyse la question et génère un plan (table, colonnes, filtres) |
|  Answer Synthesizer LLM | Retourne une réponse formatée à partir des données récupérées |
|  Dataverse Client | Authentification + récupération d'entités |
|  Extraction Schema Loader | Liste dynamique des tables et entitysets |
|  Lancement du backend | FastAPI server, endpoints RAG-like |

---

##  Tech Stack

- Python + FastAPI
- Microsoft Dataverse REST API
- Gemini LLM (Google AI)
- OData Query Builder & Dynamic EntitySets Loader

---

##  Structure du projet
dataverse-agent/output
├── answer_synthesizer.py
├── dataverse_client.py
├── llm_client.py
├── query_planner.py
├── schema_loader.py
├── odata_builder.py
├── main.py # Server FastAPI (start here)
├── requirements.txt
└── .gitignore # .env excluded for security

 Fichier `.env` (non inclus volontairement)

Crée ton fichier `.env` localement :

DATAVERSE_URL=
DATAVERSE_TENANT_ID=
DATAVERSE_CLIENT_ID=
CLIENT_SECRET= # jamais pushé
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash

=> lancer le projet:
pip install -r requirements.txt
.venv\Scripts\activate  
uvicorn main:app --reload

url 
127.0.0.1:8000



