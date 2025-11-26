# answer_synthesizer.py
import json


def synthesize_answer(llm_client, user_question: str, dataverse_result: dict) -> str:
    system_prompt = """
Tu es un assistant métier.
Tu dois répondre à la question de l'utilisateur UNIQUEMENT à partir des données fournies ci-dessous.
Si les données sont vides, dis que tu ne trouves pas la réponse.
"""

    user_prompt = f"""
QUESTION UTILISATEUR :
{user_question}

RÉSULTATS DATAVERSE (JSON) :
{json.dumps(dataverse_result, indent=2, ensure_ascii=False)}
"""

    return llm_client.chat(system=system_prompt, user=user_prompt)
