# query_planner.py
import json
import re
from typing import Dict, Any, List
from loguru import logger


def extract_json(text: str):
    """
    Essaye d’extraire un JSON valide à partir d’un texte retourné par le LLM.
    1) Tentative directe json.loads
    2) Sinon, recherche du premier bloc {...} et tentative de parse
    """
    # Tentative directe
    try:
        return json.loads(text)
    except Exception:
        pass

    # Tentative via un bloc {...}
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            pass

    return None


def build_query_plan(llm_client, user_question: str, schema_summary: Dict[str, Any]) -> dict:
    """
    Construit un plan de requête OData à partir d'une question utilisateur.

    schema_summary doit contenir :
      - "schema_text": str         → résumé texte du schéma Dataverse
      - "allowed_tables": List[str] → EntitySetName exact Dataverse (ex: "crca6_account1s")
    """
    schema_text: str = schema_summary.get("schema_text", "")
    allowed_tables: List[str] = schema_summary.get("allowed_tables") or []

    if not allowed_tables:
        raise ValueError("Aucune table autorisée (allowed_tables est vide dans schema_summary).")

    # Liste lisible pour le LLM
    allowed_text = "\n".join(f"- {t}" for t in allowed_tables)

    # ---------------------------------------------------------
    # PROMPT SYSTEM
    # ---------------------------------------------------------
    prompt_system = f"""
Tu es un planificateur de requêtes OData pour Dataverse.

Ton rôle :
- Lire le SCHÉMA (tables, colonnes, relations).
- Comprendre la question métier.
- Construire un PLAN DE REQUÊTE OData sous forme de JSON.
- Ce plan sera ensuite converti en URL OData par un autre composant.

⚠️ RÈGLES OBLIGATOIRES :

1) CHOIX DE LA TABLE
- Tu DOIS choisir la table (EntitySetName) STRICTEMENT parmi cette liste :

{allowed_text}

- N'invente JAMAIS de table (pas de "accounts", "contacts", "users", etc. hors de cette liste).
- Le champ "table" dans le JSON doit contenir exactement un EntitySetName (ex : "crca6_tickets").

2) RELATIONS & LOOKUPS (TRÈS IMPORTANT)
- Dans le SCHÉMA, certaines colonnes ont un nom qui se termine par "_value" (ex : "_crca6_accountname_value") : ce sont des GUID de lookup.
- Pour interroger un champ de la table liée (ex : le nom du compte), tu NE DOIS PAS utiliser "_xxx_value/..." car c'est invalide en OData.
- Tu dois utiliser la NavigationProperty correspondante (ex : "crca6_accountName") avec $expand.

Exemple conceptuel :
- EntityType "crca6_ticket" contient :
  - Property "_crca6_accountname_value" (Guid)
  - NavigationProperty "crca6_accountName" vers l'entité "crca6_account1"
- EntityType "crca6_account1" contient :
  - Property "crca6_name" (nom du compte)

Dans ce cas, pour filtrer les tickets par nom de compte "ACME Corporation", tu dois produire :
- "expand": "crca6_accountName($select=crca6_name)"
- "filters": "crca6_accountName/crca6_name eq 'ACME Corporation'"

3) FORMAT DU PLAN (JSON UNIQUEMENT)
- Tu renvoies UNIQUEMENT un JSON valide, sans texte autour.
- Format attendu (champs obligatoires) :

{{
  "table": "<EntitySetName principal>",
  "select": ["colonne1", "colonne2"],
  "filters": "expression OData ou null",
  "expand": "expression $expand ou null",
  "aggregation": "none",        // ou autre si besoin plus tard
  "order_by": "colonne asc|desc ou null",
  "top": 50                     // nombre max de lignes
}}

4) COMPORTEMENT GÉNÉRAL
- Si la question mélange plusieurs tables, choisis celle qui est la plus naturelle comme table principale (ex : tickets, opportunités, comptes…).
- Si tu as besoin d'un champ d'une table liée, utilise toujours une NavigationProperty avec un $expand et un filtre de type navigation/colonne.
- Si tu n'as pas besoin d'une relation, laisse "expand": null.
- Ne renvoie JAMAIS autre chose que le JSON du plan.
"""

    # ---------------------------------------------------------
    # PROMPT UTILISATEUR
    # ---------------------------------------------------------
    prompt_user = f"""
SCHÉMA:
{schema_text}

QUESTION UTILISATEUR:
{user_question}

Ta tâche :
- Lire le schéma
- Identifier la table la plus pertinente parmi la liste autorisée
- Déduire les colonnes à sélectionner
- Déduire les filtres éventuels
- Déduire les éventuels $expand nécessaires
- Produire STRICTEMENT un JSON valide conforme au format demandé.
- Ne pas ajouter de texte avant ou après le JSON.

Réponds UNIQUEMENT en JSON.
"""

    # ---------------------------------------------------------
    # 1) Appel LLM
    # ---------------------------------------------------------
    raw = llm_client.chat(system=prompt_system, user=prompt_user)
    logger.info("Réponse brute LLM (Query Planner) : " + raw)

    # ---------------------------------------------------------
    # 2) Extraction propre du JSON
    # ---------------------------------------------------------
    plan = extract_json(raw)

    if plan is None or not isinstance(plan, dict):
        logger.error(f"❌ Le LLM n'a pas renvoyé un JSON valide.\nRéponse reçue:\n{raw}")
        raise ValueError("Le LLM n’a pas renvoyé un plan JSON valide pour la requête.")

    # ---------------------------------------------------------
    # 3) Validation de la table
    # ---------------------------------------------------------
    table = plan.get("table")
    if not table or table not in allowed_tables:
        logger.error(
            "❌ Table inconnue ou interdite dans le plan : %r (tables autorisées: %r)",
            table,
            allowed_tables,
        )
        raise ValueError(
            f"❌ Table inconnue ou interdite dans le plan : {table}\n"
            f"Tables autorisées : {allowed_tables}"
        )

    # ---------------------------------------------------------
    # 4) Normalisation et valeurs par défaut
    # ---------------------------------------------------------

    # SELECT
    if "select" not in plan or not isinstance(plan["select"], list):
        plan["select"] = []

    # FILTERS
    if "filters" not in plan or plan["filters"] in ["", "none", None]:
        plan["filters"] = None

    # EXPAND
    if "expand" not in plan or plan["expand"] in ["", "none", None]:
        plan["expand"] = None

    # AGGREGATION
    if "aggregation" not in plan or plan["aggregation"] in ["", None]:
        plan["aggregation"] = "none"

    # ORDER BY
    if "order_by" not in plan or plan["order_by"] in ["", None]:
        plan["order_by"] = None

    # TOP
    if "top" not in plan:
        plan["top"] = 50  # valeur par défaut (nombre max de lignes)
    else:
        try:
            plan["top"] = int(plan["top"])
        except Exception:
            plan["top"] = 50

    return plan
