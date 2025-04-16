from http.server import BaseHTTPRequestHandler
from datetime import datetime
import json
import sys
import os

# Add the parent directory to the path so we can import mlb_hr_tracker
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mlb_hr_tracker import post_daily_summary

def run_post_summary():
    """Post the daily summary of home runs"""
    result = post_daily_summary()
    return {
        "timestamp": datetime.now().isoformat(),
        "success": result["success"]
    }

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests to the endpoint"""
        try:
            result = run_post_summary()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        except Exception as e:
            error_message = {"error": str(e)}
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(error_message).encode())

def handler(event, context):
    """Handler for serverless function invocation"""
    return run_post_summary()
