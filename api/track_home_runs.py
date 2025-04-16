from http.server import BaseHTTPRequestHandler
from datetime import datetime
import json
import sys
import os

# Add the parent directory to the path so we can import mlb_hr_tracker
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mlb_hr_tracker import init_tracker

def run_tracker():
    """Run the MLB Home Run Tracker and return results"""
    tracker = init_tracker()
    results = tracker.check_for_home_runs()
    return {
        "timestamp": datetime.now().isoformat(),
        "home_runs_found": len(results),
        "results": results
    }

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests to the endpoint"""
        try:
            result = run_tracker()
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
    return run_tracker()
