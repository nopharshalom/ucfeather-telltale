import functions_framework
from google.cloud import bigquery

client = bigquery.Client()

@functions_framework.http
def get_trend(request):
    # This query targets the absolute latest data available in the public set
    query = """
        SELECT term FROM `bigquery-public-data.google_trends.top_terms`
        WHERE refresh_date = (SELECT MAX(refresh_date) FROM `bigquery-public-data.google_trends.top_terms`)
        ORDER BY rank ASC LIMIT 1
    """
    try:
        query_job = client.query(query)
        result = next(iter(query_job.result()))
        return result.term
    except Exception as e:
        return f"Error: {str(e)}", 500