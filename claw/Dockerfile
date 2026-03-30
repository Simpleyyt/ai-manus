FROM ghcr.io/openclaw/openclaw:latest

# Switch to root to install plugin dependencies
USER root

# Setup manus-claw plugin
RUN mkdir -p /home/node/.openclaw/extensions/manus-claw
COPY manus-claw/ /home/node/.openclaw/extensions/manus-claw/
RUN cd /home/node/.openclaw/extensions/manus-claw && npm install --production
RUN chown -R node:node /home/node/.openclaw

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Switch back to non-root user
USER node

# Expose manus-claw HTTP server port and OpenClaw gateway port
EXPOSE 18788
EXPOSE 18789

# Environment variables with defaults
ENV CLAW_TTL_SECONDS=0
ENV MANUS_API_BASE_URL=""
ENV MANUS_API_KEY=""
ENV OPENCLAW_GATEWAY_TOKEN=""

ENTRYPOINT ["/entrypoint.sh"]
