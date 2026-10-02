"""Shared Google API helpers (Search Console / GA4) using the service account in GOOGLE_SA_KEY_JSON."""
import base64, json, os
from google.oauth2 import service_account

SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/analytics.readonly",
]

def credentials():
    raw = os.environ["GOOGLE_SA_KEY_JSON"].strip()
    try:
        info = json.loads(raw)
    except ValueError:
        info = json.loads(base64.b64decode(raw))
    return service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
