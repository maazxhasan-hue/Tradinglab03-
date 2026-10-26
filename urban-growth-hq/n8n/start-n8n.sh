#!/bin/sh
set -eu
mkdir -p /tmp/urban-growth-workflows
if [ -f /home/node/.n8n/urban-growth-lead-intake-imported ]; then
  echo 'Urban Growth lead workflow import marker exists; skipping import.'
else
  n8n import:workflow --input=/opt/urban-growth/workflows/urban-growth-lead-intake.json
  touch /home/node/.n8n/urban-growth-lead-intake-imported
fi
exec n8n start
