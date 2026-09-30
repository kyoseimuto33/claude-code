"""Monthly GA4 metrics per property: sessions, users, purchases, revenue, organic sessions."""
import sys
from gapi import credentials
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    RunReportRequest, DateRange, Dimension, Metric, FilterExpression, Filter)

def monthly(prop, start, end, organic=False):
    client = BetaAnalyticsDataClient(credentials=credentials())
    req = RunReportRequest(
        property=f"properties/{prop}",
        date_ranges=[DateRange(start_date=start, end_date=end)],
        dimensions=[Dimension(name="yearMonth")],
        metrics=[Metric(name=m) for m in ["sessions", "totalUsers", "ecommercePurchases", "purchaseRevenue"]],
    )
    if organic:
        req.dimension_filter = FilterExpression(filter=Filter(
            field_name="sessionDefaultChannelGroup",
            string_filter=Filter.StringFilter(value="Organic Search")))
    rows = client.run_report(req).rows
    return sorted((r.dimension_values[0].value, [v.value for v in r.metric_values]) for r in rows)

if __name__ == "__main__":
    start, end = sys.argv[1], sys.argv[2]
    for prop in sys.argv[3:]:
        for org in (False, True):
            print(f"== {prop} {'organic' if org else 'all'} (sessions, users, purchases, revenue)")
            for ym, vals in monthly(prop, start, end, org):
                print(ym, *vals)
