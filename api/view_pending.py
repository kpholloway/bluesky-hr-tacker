from http.server import BaseHTTPRequestHandler
import json
import sys
import os

# Add the parent directory to the path so we can import mlb_hr_tracker
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mlb_hr_tracker import init_tracker

def get_pending_hrs():
    """Get the list of pending home runs"""
    tracker = init_tracker()
    pending_hrs = tracker.load_pending_hrs()
    
    return {
        "pending_count": len(pending_hrs),
        "pending_hrs": pending_hrs
    }

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests to the endpoint"""
        try:
            result = get_pending_hrs()
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
    return get_pending_hrs()
