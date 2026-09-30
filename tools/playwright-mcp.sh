#!/usr/bin/env bash
# Launch Playwright MCP with the preinstalled Chromium, routed through the session proxy.
# --no-sandbox is required because the cloud container runs as root.
exec npx -y @playwright/mcp@latest \
  --headless --isolated --no-sandbox \
  --executable-path /opt/pw-browsers/chromium \
  ${HTTPS_PROXY:+--proxy-server "$HTTPS_PROXY"} "$@"
