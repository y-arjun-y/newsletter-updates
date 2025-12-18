import os
import feedparser
import requests
import datetime
from dateutil import parser
from datetime import timezone

# --- CONFIGURATION ---
# 1. List your Substacks here (use the main URL, we append /feed automatically)
SUBSTACKS = [
    "https://newsletter.pragmaticengineer.com",
    "https://www.lennysnewsletter.com",
]

# 2. Get the Webhook URL from GitHub Secrets
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

# 3. Time Window: How far back to check? (Last 70 mins to be safe for hourly runs)
TIME_WINDOW_MINUTES = 70


def send_notification(title, link, author):
    """Sends a message to the channel via Webhook."""
    if not WEBHOOK_URL:
        print("❌ Error: Webhook URL not found in environment variables.")
        return

    # Message format for Discord. (Change 'content' to 'text' if using Slack)
    payload = {"content": f"**New Post from {author}!**\n{title}\n{link}"}

    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print(f"✅ Notification sent for: {title}")
    except Exception as e:
        print(f"❌ Failed to send notification: {e}")


def check_feed(url):
    # Construct RSS feed URL (Substack usually just needs /feed appended)
    feed_url = f"{url.rstrip('/')}/feed"
    print(f"🔍 Checking: {feed_url}...")

    feed = feedparser.parse(feed_url)

    if not feed.entries:
        print("   No entries found or error parsing feed.")
        return

    # Get current time in UTC
    now = datetime.datetime.now(timezone.utc)
    cutoff = now - datetime.timedelta(minutes=TIME_WINDOW_MINUTES)

    for entry in feed.entries:
        # Parse the publication time
        try:
            published_time = parser.parse(entry.published)
        except:
            continue

        # Logic: If the post is NEWER than the cutoff time, send it.
        if published_time > cutoff:
            print(f"   🚀 FOUND NEW POST: {entry.title}")
            send_notification(entry.title, entry.link, feed.feed.title)
        else:
            # Since RSS feeds are chronological, if we hit an old one, we can stop.
            break


if __name__ == "__main__":
    print(f"--- Starting Check at {datetime.datetime.now()} ---")
    if not WEBHOOK_URL:
        print("⚠️  WARNING: No Webhook URL found. Notifications will fail.")

    for url in SUBSTACKS:
        check_feed(url)

    print("--- Check Complete ---")
