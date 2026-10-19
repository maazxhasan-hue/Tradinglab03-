# Harvey Worker (Nexora)

A small persistent API for business-listing discovery, saved prospect records, task history, and approval-gated outreach drafts.

## Deploy with Render

1. In Render, create a **Blueprint** from this repository and select the root `render.yaml`.
2. Render will create a private API key value for `HARVEY_API_KEY` and a persistent disk for SQLite.
3. After deployment, test `https://YOUR-SERVICE.onrender.com/health`.
4. In the private Harvey dashboard, set the runtime URL to that HTTPS service and paste the generated `HARVEY_API_KEY` in the token field.
5. Test prospect discovery and inspect saved prospects and draft approvals.

The blueprint is committed as configuration; it does not create a Render service until the repository is connected and the Blueprint is applied in Render.

## Endpoints

- `GET /health` — unauthenticated health check; reports that email sending is disabled.
- `GET /metrics` — authenticated counts.
- `POST /prospects/discover` — authenticated OpenStreetMap listing discovery. JSON: `{"city":"Bengaluru","category":"business","limit":15}`.
- `GET /prospects` — authenticated saved prospects.
- `POST /outreach/draft` — authenticated draft creation. JSON: `{"prospect_id":1,"service":"website improvements","value_proposition":"A concrete value proposition."}`.
- `GET /approvals` — authenticated draft approval queue.
- `POST /approvals/{id}/decision` — authenticated `{"decision":"approve"}` or `{"decision":"reject"}`.
- `GET /tasks` — authenticated task history.

All protected routes require the `X-API-Key` header. CORS is limited to the Nexora HQ production origins configured in `ALLOWED_ORIGINS` (override that environment variable if the dashboard has a different URL).

## Safety boundaries

This service does not send email, purchase leads, or access private accounts. Prospect data from OpenStreetMap may be incomplete; verify listings before contact. Email drafts require human review. Approval is a record only, not a send action. Use only compliant, honest outreach and honor opt-outs.

## Local test

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r harvey-worker/requirements.txt
HARVEY_API_KEY=local-test-key DATABASE_PATH=./harvey.db uvicorn harvey-worker.app:app --reload
```

For local execution, run from the repository root with `uvicorn app:app --app-dir harvey-worker --reload` instead of the module form above, because the directory name contains a hyphen.
