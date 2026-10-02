"""Monthly Search Console clicks, impressions, CTR and average position for a domain.

Usage: python3 gsc_monthly.py <domain> <start YYYY-MM-DD> <end YYYY-MM-DD>
       e.g. python3 gsc_monthly.py shouldagg.jp 2026-03-01 2026-09-30
Tries sc-domain:<domain>, then https://www.<domain>/ and https://<domain>/.
"""
import sys
from collections import defaultdict
from gapi import credentials
from googleapiclient.discovery import build

domain, start, end = sys.argv[1:4]
sc = build('searchconsole', 'v1', credentials=credentials(), cache_discovery=False)
owned = {s['siteUrl'] for s in sc.sites().list().execute().get('siteEntry', [])}
site = next((c for c in (f'sc-domain:{domain}', f'https://www.{domain}/', f'https://{domain}/') if c in owned), None)
if not site:
    sys.exit(f'{domain} is not shared with the service account: add it to the Search Console property (フル)')

rows = sc.searchanalytics().query(siteUrl=site, body={
    'startDate': start, 'endDate': end, 'dimensions': ['date'], 'rowLimit': 25000}).execute().get('rows', [])
m = defaultdict(lambda: [0, 0, 0.0])  # clicks, impressions, position*impressions
for r in rows:
    k = r['keys'][0][:7]
    m[k][0] += r['clicks']; m[k][1] += r['impressions']; m[k][2] += r['position'] * r['impressions']
print(f'# {site} (month clicks impressions ctr avg_position)')
for k in sorted(m):
    c, i, p = m[k]
    print(k, int(c), int(i), f'{c / i:.2%}' if i else '-', f'{p / i:.1f}' if i else '-')
