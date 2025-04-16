import time
import logging
from datetime import datetime, timedelta
import requests
from statsapi import stats, schedule

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("hr_tracker.log"), logging.StreamHandler()]
)
logger = logging.getLogger("MLB-HR-Tracker")

# Bluesky API configuration
# Note: You'll need to fill in these values with your actual credentials
BLUESKY_API_URL = "https://bsky.social/xrpc"
# These would need to be set by the user of this code
BLUESKY_USERNAME = "your_username"  
BLUESKY_APP_PASSWORD = "your_app_password"  

class BlueskyClient:
    def __init__(self, api_url, username, app_password):
        self.api_url = api_url
        self.username = username
        self.app_password = app_password
        self.session = requests.Session()
        self.jwt = None
        self.did = None
    
    def login(self):
        """Authenticate with Bluesky and get JWT token"""
        try:
            response = self.session.post(
                f"{self.api_url}/com.atproto.server.createSession",
                json={"identifier": self.username, "password": self.app_password}
            )
            response.raise_for_status()
            data = response.json()
            self.jwt = data["accessJwt"]
            self.did = data["did"]
            self.session.headers.update({"Authorization": f"Bearer {self.jwt}"})
            logger.info(f"Successfully logged in as {self.username}")
            return True
        except Exception as e:
            logger.error(f"Failed to login to Bluesky: {e}")
            return False
    
    def create_post(self, text):
        """Create a post on Bluesky"""
        if not self.jwt:
            if not self.login():
                return False
        
        try:
            now = datetime.now().isoformat()
            post_data = {
                "repo": self.did,
                "collection": "app.bsky.feed.post",
                "record": {
                    "$type": "app.bsky.feed.post",
                    "text": text,
                    "createdAt": now
                }
            }
            
            response = self.session.post(
                f"{self.api_url}/com.atproto.repo.createRecord",
                json=post_data
            )
            response.raise_for_status()
            logger.info(f"Successfully posted to Bluesky: {text}")
            return True
        except Exception as e:
            logger.error(f"Failed to post to Bluesky: {e}")
            return False

class MLBHomeRunTracker:
    def __init__(self, bluesky_client=None):
        self.bluesky_client = bluesky_client
        self.tracked_hrs = set()  # Store unique identifiers for HRs we've already posted
        
    def get_todays_games(self):
        """Get today's MLB games"""
        today = datetime.now().strftime('%m/%d/%Y')
        games = schedule(date=today)
        return games
    
    def get_game_events(self, game_id):
        """Get play-by-play events for a specific game"""
        try:
            # Get play-by-play data
            pbp_data = stats(endpoint=f"game_playByPlay", params={"gamePk": game_id})
            if not pbp_data or "allPlays" not in pbp_data:
                return []
            
            return pbp_data["allPlays"]
        except Exception as e:
            logger.error(f"Error getting game events for game {game_id}: {e}")
            return []
    
    def find_home_runs(self, game_id, events):
        """Find home run events in the play-by-play data"""
        home_runs = []
        
        for play in events:
            # Skip if we've already processed this play
            play_id = f"{game_id}_{play.get('atBatIndex')}"
            if play_id in self.tracked_hrs:
                continue
                
            # Check if this is a home run
            result = play.get("result", {})
            description = result.get("description", "").lower()
            event = result.get("event", "").lower()
            
            if "home run" in event:
                # Extract player info
                player_name = play.get("matchup", {}).get("batter", {}).get("fullName", "Unknown Player")
                team_name = play.get("matchup", {}).get("batter", {}).get("team", {}).get("name", "Unknown Team")
                
                # Get the player's season HR total
                # This would require an additional API call to get the player's stats
                # For simplicity, we'll just include a placeholder
                hr_count = self.get_player_hr_count(play.get("matchup", {}).get("batter", {}).get("id"))
                
                home_runs.append({
                    "play_id": play_id,
                    "player_name": player_name,
                    "team_name": team_name,
                    "hr_count": hr_count,
                    "description": description
                })
                
                # Mark this HR as tracked
                self.tracked_hrs.add(play_id)
                
        return home_runs
    
    def get_player_hr_count(self, player_id):
        """Get a player's season home run total"""
        try:
            # Get player stats for the current season
            player_stats = stats(endpoint="person_stats", params={"personId": player_id, "stats": "season"})
            
            # Extract HR count from stats
            stats_data = player_stats.get("stats", [{}])[0].get("splits", [{}])[0].get("stat", {})
            hr_count = stats_data.get("homeRuns", 0)
            
            return hr_count
        except Exception as e:
            logger.error(f"Error getting HR count for player {player_id}: {e}")
            return "?"  # Return placeholder if we can't get the count
    
    def format_hr_post(self, hr_data):
        """Format a home run event as a social media post"""
        return f"HOME RUN! {hr_data['player_name']} ({hr_data['team_name']}) hits home run #{hr_data['hr_count']} of the season! {hr_data['description']}"
    
    def post_home_run(self, hr_data):
        """Post a home run to Bluesky"""
        if not self.bluesky_client:
            logger.info(f"Would post to Bluesky: {self.format_hr_post(hr_data)}")
            return True
            
        post_text = self.format_hr_post(hr_data)
        return self.bluesky_client.create_post(post_text)
    
    def check_for_home_runs(self):
        """Check for new home runs in today's games"""
        games = self.get_todays_games()
        
        for game in games:
            game_id = game.get("game_id")
            game_status = game.get("status")
            
            # Only check games that are in progress or recently finished
            if game_status in ["In Progress", "Final"]:
                events = self.get_game_events(game_id)
                home_runs = self.find_home_runs(game_id, events)
                
                for hr in home_runs:
                    logger.info(f"Found new home run: {hr['player_name']} ({hr['team_name']})")
                    self.post_home_run(hr)

def main():
    # Create Bluesky client (commented out - user would need to fill in credentials)
    # bluesky_client = BlueskyClient(
    #     api_url=BLUESKY_API_URL,
    #     username=BLUESKY_USERNAME,
    #     app_password=BLUESKY_APP_PASSWORD
    # )
    
    # For testing without posting, pass None as the client
    tracker = MLBHomeRunTracker(bluesky_client=None)
    
    logger.info("Starting MLB Home Run Tracker")
    
    try:
        while True:
            logger.info("Checking for home runs...")
            tracker.check_for_home_runs()
            
            # Wait 60 seconds before checking again
            logger.info("Waiting 60 seconds before next check...")
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down MLB Home Run Tracker")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

if __name__ == "__main__":
    main()