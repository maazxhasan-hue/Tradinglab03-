FROM n8nio/n8n:latest
USER root
RUN mkdir -p /opt/urban-growth/workflows
COPY urban-growth-hq/n8n/urban-growth-lead-intake.json /opt/urban-growth/workflows/urban-growth-lead-intake.json
COPY urban-growth-hq/n8n/nexora-shared-brain-health-monitor.json /opt/urban-growth/workflows/nexora-shared-brain-health-monitor.json
COPY urban-growth-hq/n8n/start-n8n.js /opt/urban-growth/start-n8n.js
RUN chown -R node:node /opt/urban-growth
USER node
ENV PORT=5678
ENV N8N_PORT=5678
ENV N8N_LISTEN_ADDRESS=0.0.0.0
ENV N8N_RUNNERS_ENABLED=false
ENTRYPOINT ["/usr/local/bin/node", "/opt/urban-growth/start-n8n.js"]
