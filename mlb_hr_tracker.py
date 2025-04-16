import logging
from datetime import datetime, timezone
import requests
import os
import json
from statsapi import stats, schedule

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("/tmp/hr_tracker.log"), logging.StreamHandler()]
)
logger = logging.getLogger("MLB-HR-Tracker")

# Bluesky API configuration from environment variables
BLUESKY_API_URL = "https://bsky.social/xrpc"
BLUESKY_USERNAME = os.environ.get("BLUESKY_USERNAME")
BLUESKY_APP_PASSWORD = os.environ.get("BLUESKY_APP_PASSWORD")

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
    
    def create_post(self, text, created_at=None):
        """Create a post on Bluesky with optional timestamp"""
        if not self.jwt:
            if not self.login():
                return False
        
        try:
            # Use provided timestamp or current time
            if created_at is None:
                created_at = datetime.now(timezone.utc).isoformat()
            # Ensure the timestamp is in ISO format
            elif isinstance(created_at, datetime):
                created_at = created_at.astimezone(timezone.utc).isoformat()
                
            post_data = {
                "repo": self.did,
                "collection": "app.bsky.feed.post",
                "record": {
                    "$type": "app.bsky.feed.post",
                    "text": text,
                    "createdAt": created_at
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
        self.tracked_hrs_file = "/tmp/tracked_hrs.json"
        self.pending_hrs_file = "/tmp/pending_hrs.json"
        self.tracked_hrs = self.load_tracked_hrs()
        self.pending_hrs = self.load_pending_hrs()
        
    def load_tracked_hrs(self):
        """Load tracked home runs from file storage"""
        try:
            with open(self.tracked_hrs_file, "r") as f:
                return set(json.load(f))
        except:
            return set()
    
    def save_tracked_hrs(self):
        """Save tracked home runs to file storage"""
        with open(self.tracked_hrs_file, "w") as f:
            json.dump(list(self.tracked_hrs), f)
    
    def load_pending_hrs(self):
        """Load pending home runs that need to be posted"""
        try:
            with open(self.pending_hrs_file, "r") as f:
                return json.load(f)
        except:
            return []
    
    def save_pending_hrs(self):
        """Save pending home runs to file storage"""
        with open(self.pending_hrs_file, "w") as f:
            json.dump(self.pending_hrs, f)
    
    def add_pending_hr(self, hr_data):
        """Add a home run to the pending list"""
        self.pending_hrs.append(hr_data)
        self.save_pending_hrs()
    
    def clear_pending_hrs(self):
        """Clear the pending home runs after posting"""
        self.pending_hrs = []
        self.save_pending_hrs()
    
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
                hr_count = self.get_player_hr_count(play.get("matchup", {}).get("batter", {}).get("id"))
                
                # Extract timestamp from play data, or use current time if not available
                timestamp = None
                try:
                    if "about" in play and "endTime" in play["about"]:
                        timestamp_str = play["about"]["endTime"]
                        timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                    else:
                        timestamp = datetime.now()
                except Exception as e:
                    logger.error(f"Error parsing timestamp: {e}")
                    timestamp = datetime.now()
                
                home_run_data = {
                    "play_id": play_id,
                    "player_name": player_name,
                    "team_name": team_name,
                    "hr_count": hr_count,
                    "description": description,
                    "timestamp": timestamp.isoformat()
                }
                
                home_runs.append(home_run_data)
                
                # Mark this HR as tracked
                self.tracked_hrs.add(play_id)
                
                # Add to pending list for batched posting
                self.add_pending_hr(home_run_data)
                
        # Save tracked HRs if any new ones were found
        if home_runs:
            self.save_tracked_hrs()
                
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
        # Format timestamp
        try:
            timestamp = datetime.fromisoformat(hr_data['timestamp'])
            time_str = timestamp.strftime("%I:%M %p")
        except:
            time_str = "Unknown time"
            
        return f"HOME RUN! {hr_data['player_name']} ({hr_data['team_name']}) hits home run #{hr_data['hr_count']} of the season at {time_str}! {hr_data['description']}"
    
    def post_individual_home_run(self, hr_data):
        """Post a single home run to Bluesky"""
        if not self.bluesky_client:
            logger.info(f"Would post to Bluesky: {self.format_hr_post(hr_data)}")
            return True
            
        post_text = self.format_hr_post(hr_data)
        # Get timestamp from the HR data
        try:
            timestamp = datetime.fromisoformat(hr_data['timestamp'])
        except:
            timestamp = None
            
        return self.bluesky_client.create_post(post_text, created_at=timestamp)
    
    def format_daily_summary(self, hrs_list):
        """Format a daily summary of home runs"""
        if not hrs_list:
            return "No home runs recorded today."
            
        # Sort by timestamp
        sorted_hrs = sorted(hrs_list, key=lambda x: x.get('timestamp', ''))
        
        # Create the summary
        summary = f"MLB HOME RUN DAILY SUMMARY - {datetime.now().strftime('%Y-%m-%d')}\n\n"
        
        for idx, hr in enumerate(sorted_hrs, 1):
            try:
                timestamp = datetime.fromisoformat(hr['timestamp'])
                time_str = timestamp.strftime("%I:%M %p")
            except:
                time_str = "Unknown time"
                
            summary += f"{idx}. {time_str}: {hr['player_name']} ({hr['team_name']}) - HR #{hr['hr_count']}\n"
            
            # Bluesky has character limits, if we're approaching it, add "..." and stop
            if len(summary) > 280 and idx < len(sorted_hrs):
                summary += f"... and {len(sorted_hrs) - idx} more home runs."
                break
                
        return summary
    
    def post_daily_summary(self):
        """Post a daily summary of all home runs to Bluesky"""
        pending_hrs = self.load_pending_hrs()
        
        if not pending_hrs:
            logger.info("No pending home runs to post in daily summary")
            return False
            
        if not self.bluesky_client:
            logger.info(f"Would post daily summary to Bluesky:\n{self.format_daily_summary(pending_hrs)}")
            return True
            
        # Create and post the summary
        summary_text = self.format_daily_summary(pending_hrs)
        success = self.bluesky_client.create_post(summary_text)
        
        if success:
            logger.info(f"Posted daily summary with {len(pending_hrs)} home runs")
            # Clear pending home runs after successful posting
            self.clear_pending_hrs()
            
        return success
    
    def check_for_home_runs(self, post_type='individual'):
        """
        Check for new home runs in today's games
        post_type: 'individual' posts each HR as it happens, 'collect' saves for daily summary
        """
        results = []
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
                    
                    # Post immediately if individual mode
                    if post_type == 'individual':
                        success = self.post_individual_home_run(hr)
                        results.append({
                            "player": hr['player_name'],
                            "team": hr['team_name'],
                            "posted": success
                        })
        
        return results
    
    def post_summary(self):
        """Post summary of collected home runs"""
        return self.post_daily_summary()

def init_tracker():
    """Initialize the tracker with or without Bluesky client"""
    # Only initialize the Bluesky client if credentials are available
    bluesky_client = None
    if BLUESKY_USERNAME and BLUESKY_APP_PASSWORD:
        bluesky_client = BlueskyClient(
            api_url=BLUESKY_API_URL,
            username=BLUESKY_USERNAME,
            app_password=BLUESKY_APP_PASSWORD
        )
    
    return MLBHomeRunTracker(bluesky_client=bluesky_client)

def check_home_runs():
    """Check for new home runs and collect them for later posting"""
    tracker = init_tracker()
    logger.info("Checking for new MLB home runs")
    results = tracker.check_for_home_runs(post_type='collect')
    logger.info(f"Found and processed {len(results)} home runs")
    return results

def post_daily_summary():
    """Post daily summary of all collected home runs"""
    tracker = init_tracker()
    logger.info("Posting daily summary of MLB home runs")
    success = tracker.post_summary()
    return {"success": success}

def main():
    """Run the tracker once for testing or CLI use"""
    tracker = init_tracker()
    logger.info("Running MLB Home Run Tracker")
    
    # Default: check for HRs and collect them
    results = tracker.check_for_home_runs(post_type='collect')
    logger.info(f"Found and processed {len(results)} home runs")
    
    # Optional: post daily summary for testing
    # success = tracker.post_summary()
    # logger.info(f"Daily summary posted: {success}")
    
    return results

if __name__ == "__main__":
    main()
