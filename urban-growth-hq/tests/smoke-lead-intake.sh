#!/usr/bin/env bash
# Smoke-test the deployed Urban Growth HQ lead intake.
# Uses synthetic data only. Requires curl and Python 3.
set -euo pipefail

BASE_URL="${BASE_URL:-https://urban-growth-n8n.onrender.com}"
WEBHOOK="$BASE_URL/webhook/urban-growth-hq-lead-intake"
tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

post_json() {
  local payload="$1"
  curl --fail-with-body --silent --show-error --max-time 25 \
    -o "$tmp" -w '%{http_code}' \
    -X POST "$WEBHOOK" \
    -H 'Content-Type: application/json' \
    --data "$payload"
}

assert_json() {
  python3 - "$tmp" "$@" <<'PY'
import json, sys
path, expected_ok, expected_consent = sys.argv[1:]
with open(path, encoding="utf-8") as f:
    data = json.load(f)
assert data.get("ok") is (expected_ok == "true"), data
lead = data.get("lead") or {}
assert lead.get("contact_allowed") is (expected_consent == "true"), data
assert data.get("storage_status") == "not_persisted", data
print("JSON assertions passed:", data.get("status"), "consent allowed:", lead.get("contact_allowed"))
PY
}

printf 'Test 1: valid lead without consent must be accepted but not contactable... '
status="$(post_json '{"name":"UG HQ Test","email":"urban-growth-smoke@example.com","consent":false}')"
[[ "$status" == "200" ]] || { cat "$tmp"; echo "expected HTTP 200, got $status"; exit 1; }
assert_json true false

printf 'Test 2: valid lead with consent can be marked contactable... '
status="$(post_json '{"name":"UG HQ Test","email":"urban-growth-smoke@example.com","consent":true}')"
[[ "$status" == "200" ]] || { cat "$tmp"; echo "expected HTTP 200, got $status"; exit 1; }
assert_json true true

printf 'Test 3: invalid lead must be rejected... '
# curl deliberately does not use --fail here because HTTP 400 is the expected outcome.
status="$(curl --silent --show-error --max-time 25 -o "$tmp" -w '%{http_code}' \
  -X POST "$WEBHOOK" -H 'Content-Type: application/json' \
  --data '{"name":"","email":"not-an-email","consent":false}')"
[[ "$status" == "400" ]] || { cat "$tmp"; echo "expected HTTP 400, got $status"; exit 1; }
python3 - "$tmp" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    data = json.load(f)
assert data.get("ok") is False, data
assert "name_required" in data.get("errors", []), data
assert data.get("lead", {}).get("contact_allowed") is False, data
print("JSON assertions passed: invalid lead rejected")
PY

echo 'PASS: deployed lead-intake smoke tests. Note: storage is not persistent yet.'
