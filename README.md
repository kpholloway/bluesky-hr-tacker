# MLB Home Run Tracker

A serverless application that tracks MLB home runs in real-time and posts daily summaries to Bluesky.

## How It Works

1. The application uses the MLB Stats API to check for home runs in active MLB games throughout the day
2. When a home run is detected, the system collects and stores it with the exact timestamp it occurred
3. At the end of the day, all collected home runs are posted in a chronological summary to Bluesky
4. The entire application runs as serverless functions on Vercel's Hobby tier

## Components

### API Endpoints:

- `/api/check_home_runs` - Checks for new home runs and adds them to the pending list
- `/api/post_summary` - Posts a daily summary of all collected home runs to Bluesky
- `/api/view_pending` - Returns the current list of pending home runs
- `/api/status` - Shows current game statuses and tracking information

### Web Interface:

- Dashboard showing active MLB games
- List of pending home runs waiting to be included in the daily summary
- Manual buttons to check for home runs and post summaries
- Status indicators showing if Bluesky posting is enabled

## Deployment Instructions

### Prerequisites

1. A GitHub account
2. A Vercel account connected to your GitHub
3. (Optional) A Bluesky account and app password for posting updates

### Setup

1. Push this code to a GitHub repository
2. Create a new project in Vercel and import your GitHub repository
3. Select "Other" framework preset during the import process
4. Add the following environment variables in the Vercel project settings:
   - `BLUESKY_USERNAME` - Your Bluesky username
   - `BLUESKY_APP_PASSWORD` - Your Bluesky app password

### Vercel Configuration

The included `vercel.json` file configures:
- Python API routes using the "@vercel/python" runtime
- Static file serving for the web interface
- Cron jobs that run within Vercel's Hobby tier limitations:
  - Check for new home runs every 4 hours
  - Post a daily summary at 11:00 PM

## Local Development

To run the application locally:

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run the tracker manually to check for and collect home runs:
   ```
   python mlb_hr_tracker.py
   ```

3. Or test specific API endpoints using tools like Postman or curl

## Data Storage

The application uses temporary file storage for tracking home runs and maintaining the pending list. In the serverless environment, this data will be cleared periodically. For a more persistent solution, consider implementing a database connection.

## Customization

- **Posting Frequency**: Edit the cron schedule in `vercel.json` to change when checks occur
- **Post Format**: Modify the `format_daily_summary` function in `mlb_hr_tracker.py` to change the format of Bluesky posts
- **Web Interface**: Customize `index.html` to modify the dashboard appearance

## License

MIT
