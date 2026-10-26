FROM n8nio/n8n:latest
USER root
RUN mkdir -p /opt/urban-growth/workflows
COPY urban-growth-hq/n8n/urban-growth-lead-intake.json /opt/urban-growth/workflows/urban-growth-lead-intake.json
COPY urban-growth-hq/n8n/start-n8n.js /opt/urban-growth/start-n8n.js
RUN chown -R node:node /opt/urban-growth
USER node
ENTRYPOINT ["/usr/local/bin/node", "/opt/urban-growth/start-n8n.js"]
