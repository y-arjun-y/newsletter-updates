import feedparser
import requests
import json
import os
import time

# --- CONFIGURATION ---
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
STATE_FILE = "feed_state.json"

NEWSLETTERS = {
    "Thing of Things": "https://thingofthings.substack.com/feed",
    "Slow Boring": "https://www.slowboring.com/feed",
    "Astral Codex Ten": "https://www.astralcodexten.com/feed",
    "Bentham's Bulldog": "https://benthamsbulldog.substack.com/feed",
    "Celeste's Newsletter": "https://celestemarcus.substack.com/feed",
}
# ---------------------


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)


def send_discord_message(name, entry):
    print(f"Sending notification for {name}...")

    # Simple, clean Discord payload
    data = {
        "username": "Newsletter Bot",
        "embeds": [
            {
                "title": entry.title,
                "description": f"**New post from {name}**\n{entry.summary[:150]}...",
                "url": entry.link,
                "color": 16739072,  # Orange
                "footer": {"text": "Substack Notification"},
            }
        ],
    }

    try:
        requests.post(WEBHOOK_URL, json=data).raise_for_status()
    except Exception as e:
        print(f"Failed to send to Discord: {e}")


def main():
    if not WEBHOOK_URL:
        print("Error: DISCORD_WEBHOOK_URL not found.")
        return

    state = load_state()
    dirty = False

    for name, url in NEWSLETTERS.items():
        print(f"Checking {name}...")
        try:
            feed = feedparser.parse(url)
            if not feed.entries:
                continue

            latest_post = feed.entries[0]
            latest_id = latest_post.get("id", latest_post.link)

            # If we've never seen this newsletter before, just save it (don't spam)
            if name not in state:
                state[name] = latest_id
                dirty = True
                print(f"Initialized history for {name}")
                continue

            # If the ID is different, it's new!
            if state[name] != latest_id:
                send_discord_message(name, latest_post)
                state[name] = latest_id
                dirty = True
        except Exception as e:
            print(f"Error checking {name}: {e}")

    if dirty:
        save_state(state)
        print("State updated.")


if __name__ == "__main__":
    main()
