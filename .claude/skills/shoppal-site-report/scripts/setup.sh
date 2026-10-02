#!/usr/bin/env bash
# One-time setup per cloud session for the shoppal-site-report skill.
set -euo pipefail
pip install -q google-auth google-api-python-client google-analytics-data google-analytics-admin pymupdf 2>/dev/null \
  || pip install -q --ignore-installed cffi cryptography google-auth google-api-python-client google-analytics-data google-analytics-admin pymupdf
python3 -c "import google.oauth2.service_account" 2>/dev/null || pip install -q --ignore-installed cffi cryptography
npm ls -g pptxgenjs >/dev/null 2>&1 || npm install -g -q pptxgenjs >/dev/null
npx -y playwright --version >/dev/null 2>&1 || true   # caches the playwright package for pw.js

# Chromium must trust the session proxy CA (the NSS store is empty in a fresh container).
if [ -f /root/.ccr/ca-bundle.crt ]; then
  command -v certutil >/dev/null || apt-get install -y -q libnss3-tools >/dev/null 2>&1 || true
  mkdir -p "$HOME/.pki/nssdb"
  [ -f "$HOME/.pki/nssdb/cert9.db" ] || certutil -N -d "sql:$HOME/.pki/nssdb" --empty-password
  if ! certutil -L -d "sql:$HOME/.pki/nssdb" | grep -q ccr-; then
    tmp=$(mktemp -d)
    awk -v d="$tmp" '/BEGIN CERT/{n++} {print > (d "/c" n ".pem")}' /root/.ccr/ca-bundle.crt
    for f in "$tmp"/c*.pem; do certutil -A -d "sql:$HOME/.pki/nssdb" -n "ccr-$(basename "$f" .pem)" -t "C,," -i "$f" 2>/dev/null || true; done
    rm -rf "$tmp"
  fi
fi

# Japanese fonts + LibreOffice Impress for visual QA (optional; skipped if apt is unavailable).
fc-list :lang=ja | grep -qi noto || apt-get install -y -q fonts-noto-cjk >/dev/null 2>&1 || true
dpkg -s libreoffice-impress >/dev/null 2>&1 || apt-get install -y -q libreoffice-impress >/dev/null 2>&1 || true

echo "SHOPPAL_ADMIN_USER: ${SHOPPAL_ADMIN_USER:-cx@fulmo.co.jp (shared account)}"
for v in SHOPPAL_ADMIN_PASS GOOGLE_SA_KEY_JSON; do
  [ -n "${!v:-}" ] && echo "$v: set" || echo "$v: MISSING (add it in the environment settings)"
done
