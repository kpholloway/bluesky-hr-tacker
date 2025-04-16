# MLB Home Run Tracker

A serverless application that tracks MLB home runs in real-time and posts updates to Bluesky.

## How It Works

1. The application uses the MLB Stats API to check for home runs in active MLB games.
2. When a home run is detected, it automatically posts an update to Bluesky (if credentials are configured).
3. The entire application runs as serverless functions on Vercel.

## Components

- **API Endpoints:**
  - `/api/track_home_runs` - Checks for new home runs and posts updates
  - `/api/status` - Shows current game statuses and tracking information
  
- **Web Interface:**
  - Simple dashboard showing active games and recent home runs
  - Manual trigger for checking home runs

## Deployment Instructions

### Prerequisites

1. A GitHub account
2. A Vercel account connected to your GitHub
3. (Optional) A Bluesky account and app password for posting updates

### Setup

1. Push this code to a GitHub repository
2. Create a new project in Vercel and import your GitHub repository
3. Add the following environment variables in the Vercel project settings:
   - `BLUESKY_USERNAME` - Your Bluesky username
   - `BLUESKY_APP_PASSWORD` - Your Bluesky app password

### Vercel Configuration

The included `vercel.json` file configures:
- Python API routes
- Static file serving
- Cron job to automatically check for home runs every 5 minutes

## Local Development

To run the application locally:

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the tracker manually:
   ```
   python mlb_hr_tracker.py
   ```

3. Or test the API endpoints using tools like Postman or curl

## Data Storage

The application uses temporary file storage for tracking which home runs have been processed. In the serverless environment, this data will be cleared periodically. For a more persistent solution, consider implementing a database connection.

## License

MIT
