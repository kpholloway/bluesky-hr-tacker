from http.server import BaseHTTPRequestHandler
import json
import os
import sys

# Add the parent directory to the path so we can import mlb_hr_tracker
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mlb_hr_tracker import schedule

def get_status():
    """Get the current status of MLB games"""
    try:
        games = schedule()
        active_games = []
        
        for game in games:
            if game.get("status") in ["In Progress", "Final", "Pre-Game", "Scheduled"]:
                active_games.append({
                    "game_id": game.get("game_id"),
                    "status": game.get("status"),
                    "home_team": game.get("home_team", "Unknown"),
                    "away_team": game.get("away_team", "Unknown"),
                    "home_score": game.get("home_score", 0),
                    "away_score": game.get("away_score", 0)
                })
        
        return {
            "active_games": len(active_games),
            "games": active_games,
            "tracking_enabled": bool(os.environ.get("BLUESKY_USERNAME") and os.environ.get("BLUESKY_APP_PASSWORD"))
        }
    except Exception as e:
        return {"error": str(e)}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests to the endpoint"""
        result = get_status()
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

def handler(event, context):
    """Handler for serverless function invocation"""
    return get_status()
