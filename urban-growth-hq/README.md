# Urban Growth HQ — The Urban Builders

Mobile-friendly real-estate growth workspace.

## Current deployment
- Workspace: https://github.com/maazxhasan-hue/Tradinglab03-/tree/main/urban-growth-hq
- Dashboard: https://urban-growth-hq.onrender.com
- n8n: https://urban-growth-n8n.onrender.com
- Lead intake webhook (POST): https://urban-growth-n8n.onrender.com/webhook/urban-growth-hq-lead-intake

Example request:
```bash
curl -X POST "https://urban-growth-n8n.onrender.com/webhook/urban-growth-hq-lead-intake" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Lead","email":"test@example.com","interest":"2-bedroom apartment","source":"website","contactConsent":false}'
```
Use only a test contact when validating. A successful HTTP 200 means the payload passed validation; it does not mean the lead was saved or contacted.

## Workspace includes
- Responsive command centre and six-stage growth workflow
- Campaign drafts and human approval queue
- Local lead records and status tracking
- Showing and call-outcome logs
- 41 specialist role definitions across eight departments
- Rules-based operations scan, task list, activity feed
- JSON export and restore

## Smoke tests
Run `bash urban-growth-hq/tests/smoke-lead-intake.sh` from the repository root. The script uses synthetic test data and checks HTTP status, validation, consent gating, and the explicit non-persistence status. Override the endpoint with `BASE_URL` when testing a different deployment.

Latest verified live test results (2026-10-27): valid synthetic lead returns HTTP 200; invalid lead returns HTTP 400. These tests verify intake validation only, not durable CRM persistence or real outreach.

## Operational boundaries
- The 41 entries are role definitions, not 41 independently running AI agents.
- The n8n lead-intake workflow validates and normalizes contact details and records whether contact consent was supplied. It does not yet write leads to a CRM/database, perform durable deduplication, or send follow-up messages.
- The workspace currently saves records in this browser's localStorage. Data does not sync across devices and can be lost if browser storage is cleared.
- Social publishing, WhatsApp/email sending, phone calls, live AI provider execution, authentication and cloud CRM persistence are not connected.
- Approval records are internal only; approving a campaign does not publish it externally.
- Only contact people when you have the required permission and comply with applicable laws and platform rules. Do not enter highly sensitive customer data into a public deployment.

## Next production requirements
1. Connect a dedicated persistent database and CRM writes.
2. Add authenticated access and server-side authorization.
3. Connect an approved AI provider and test agent execution.
4. Connect opted-in outreach channels with rate limits, unsubscribe/opt-out handling, and human approval.
5. Test webhook acceptance/rejection and end-to-end lead persistence before describing the system as production-ready.

## Phone install and offline use
Open the deployed HTTPS workspace in Chrome on Android. Use the browser menu and choose **Install app** or **Add to Home screen** if offered. Export JSON backups regularly.
