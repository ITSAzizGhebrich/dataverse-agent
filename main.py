# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from dataverse_client import dataverse_get
from query_planner import build_query_plan
from odata_builder import build_odata_from_plan
from answer_synthesizer import synthesize_answer
from schema_loader import load_schema_summary, extract_entitysets_from_metadata
from llm_client import llm_client
from fastapi.responses import HTMLResponse

app = FastAPI()


class AskRequest(BaseModel):
    question: str




@app.post("/ask")
def ask(req: AskRequest):
    user_question = req.question

    if __name__ == "__main__":
        print("\n===== ENTITYSET MAPPING (Dataverse) =====\n")
    mapping = extract_entitysets_from_metadata()
    for logical, entityset in mapping.items():
        print(f"{logical:30} → {entityset}")

    # 1) Charger le schéma Dataverse résumé
    schema_summary = load_schema_summary()

    # 2) Construire le plan de requête (LLM)
    plan = build_query_plan(llm_client, user_question, schema_summary)

    # 3) Correction automatique du nom de table (logical → entityset)
    entity_map = extract_entitysets_from_metadata()
    logical = plan["table"]

    if logical in entity_map:
        plan["table"] = entity_map[logical]
    else:
        raise ValueError(f"❌ Table inconnue dans Dataverse : {logical}")

    # 4) Construire l’URL OData correcte
    relative_url = build_odata_from_plan(plan)

    # 5) Appeler Dataverse
    dv_result = dataverse_get(relative_url)

    # 6) Synthétiser la réponse finale
    answer = synthesize_answer(llm_client, user_question, dv_result)

    return {
        "plan": plan,               # Pour debug
        "odata": relative_url,      # La requête réelle OData
        "raw_result": dv_result,    # Résultat brut Dataverse
        "answer": answer            # Réponse finale
    }


@app.get("/", response_class=HTMLResponse)
def ui():
    return """
<!doctype html>
<html lang="fr">
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Agent Dataverse – Demo</title>

<style>
  body {
    font-family: system-ui, sans-serif;
    margin: 2rem;
    max-width: 900px;
  }
  .card {
    border: 1px solid #ddd;
    border-radius: 12px;
    padding: 1rem;
    margin-top: 1rem;
  }
  textarea {
    width: 100%;
    height: 120px;
    padding: .6rem;
    border-radius: 8px;
    border: 1px solid #bbb;
  }
  button {
    padding: .6rem 1.4rem;
    border-radius: 8px;
    border: none;
    background: #111;
    color: #fff;
    cursor: pointer;
  }
  pre {
    white-space: pre-wrap;
  }
</style>

<h1>💬 Agent Dataverse – Démo</h1>
<p class="muted">Pose ta question et l’agent va interroger Dataverse via OData.</p>

<div class="card">
  <label for="q"><b>Question :</b></label><br/>
  <textarea id="q" placeholder="Ex : Ask !"></textarea><br/><br/>
  <button onclick="ask()">Envoyer</button>
</div>

<div id="out"></div>

<script>
async function ask() {
  const q = document.getElementById('q').value.trim();
  if (!q) return;

  const res = await fetch('/ask', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({question: q})
  });

  const data = await res.json();
  const out = document.getElementById('out');
  out.innerHTML = '';

  // Réponse finale
  const ans = document.createElement('div');
  ans.className = 'card';
  ans.innerHTML = '<h3>Réponse</h3><pre>' + data.answer + '</pre>';
  out.appendChild(ans);

  // Plan JSON
  const plan = document.createElement('div');
  plan.className = 'card';
  plan.innerHTML = '<h3>Plan généré (LLM → Query)</h3><pre>' + JSON.stringify(data.plan, null, 2) + '</pre>';
  out.appendChild(plan);

  // URL OData
  const odata = document.createElement('div');
  odata.className = 'card';
  odata.innerHTML = '<h3>Requête OData</h3><pre>' + data.odata + '</pre>';
  out.appendChild(odata);

  // Résultat brut
  const raw = document.createElement('div');
  raw.className = 'card';
  raw.innerHTML = '<h3>Résultat Dataverse</h3><pre>' + JSON.stringify(data.raw_result, null, 2) + '</pre>';
  out.appendChild(raw);
}
</script>

</html>
"""
