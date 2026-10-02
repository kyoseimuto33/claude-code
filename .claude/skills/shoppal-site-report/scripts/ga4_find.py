"""Find GA4 property IDs whose name or web stream URL matches a keyword.

Usage: python3 ga4_find.py <keyword> [<keyword> ...]   e.g. python3 ga4_find.py shouldagg ショルダッグ
Property names are often katakana (e.g. ヨソジー for yosozee), so the stream URL is checked too.
"""
import sys
from gapi import credentials
from google.analytics.admin_v1beta import AnalyticsAdminServiceClient

keys = [k.lower() for k in sys.argv[1:]]
client = AnalyticsAdminServiceClient(credentials=credentials())
for acc in client.list_account_summaries():
    for p in acc.property_summaries:
        hit = any(k in p.display_name.lower() for k in keys)
        urls = []
        if not hit:
            try:
                urls = [s.web_stream_data.default_uri for s in client.list_data_streams(parent=p.property)]
            except Exception:
                urls = []
            hit = any(k in u.lower() for k in keys for u in urls)
        if hit:
            print(p.property.split('/')[-1], p.display_name, *urls, sep='\t')
