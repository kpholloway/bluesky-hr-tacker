# api/check_home_runs.py
from http.server import BaseHTTPRequestHandler
import json

def handler(request):
    # Simplified handler for Vercel serverless functions
    try:
        # Instead of importing other modules, just return a test response
        return {
            "body": json.dumps({
                "timestamp": "2025-04-16T12:00:00Z",
                "home_runs_found": 0,
                "results": [],
                "status": "API endpoint is working"
            }),
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json"
            }
        }
    except Exception as e:
        return {
            "body": json.dumps({"error": str(e)}),
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json"
            }
        }
