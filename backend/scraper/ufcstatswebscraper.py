'''
backend/scraper/ufcstatswebscraper.py

This script scrapes completed UFC events and their fight details from the UFC Stats website. It collects event names, URLs, and fight details such as fighters, results, weight classes, methods, rounds, and times. The collected data is stored in a CSV file for further analysis.

Usage:
  python3 backend/scraper/ufcstatswebscraper.py          # incremental (only new events)
  python3 backend/scraper/ufcstatswebscraper.py --full   # rescrape everything
'''

import sys
import re
import hashlib
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from tqdm import tqdm

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
OUTPUT_FILE = os.path.join(ROOT_DIR, "data/raw/ufcfights.csv")
FAILED_LOG = os.path.join(ROOT_DIR, "data/raw/failed_events.txt")
BASE_URL = "http://ufcstats.com/statistics/events/completed?page="

FULL_RESCRAPE = "--full" in sys.argv

# ufcstats.com serves a JavaScript "Checking your browser…" interstitial that
# guards the real pages behind a SHA-256 proof-of-work. A plain requests.get
# can't run JS, so we replicate the challenge here: find the smallest n where
# sha256(nonce:n) starts with the target prefix, POST it to /__c, and the
# session receives a clearance cookie. All requests share one Session so the
# cookie persists for the rest of the scrape.
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "Mozilla/5.0 (compatible; UFCEloScraper/1.0)"})

# The whole brittle challenge contract — the part most likely to break when the
# site changes — lives here together. CHALLENGE_MARKER is a bytes substring so
# the common (no-challenge) path can check response.content without decoding.
CHALLENGE_MARKER = b"Checking your browser"
CHALLENGE_ENDPOINT = "/__c"
NONCE_RE = re.compile(r'nonce="([0-9a-f]+)"')
DIFFICULTY_RE = re.compile(r"new Array\((\d+)\+1\)\.join\('0'\)")
MAX_CHALLENGE_SOLVES = 2


def _solve_challenge(url: str, html: str) -> None:
    """Solve the ufcstats.com proof-of-work interstitial so SESSION gets its cookie."""
    nonce_match = NONCE_RE.search(html)
    diff_match = DIFFICULTY_RE.search(html)
    if not nonce_match or not diff_match:
        raise RuntimeError("Anti-bot challenge detected but could not be parsed — "
                           "the site's challenge format may have changed.")
    nonce = nonce_match.group(1)
    target = "0" * int(diff_match.group(1))
    n = 0
    while not hashlib.sha256(f"{nonce}:{n}".encode()).hexdigest().startswith(target):
        n += 1
    parts = urlparse(url)
    resp = SESSION.post(f"{parts.scheme}://{parts.netloc}{CHALLENGE_ENDPOINT}",
                        data={"nonce": nonce, "n": n}, timeout=15)
    resp.raise_for_status()


def fetch_with_retry(url: str, max_retries: int = 3) -> requests.Response:
    """GET url with exponential backoff; raises immediately on 4xx, retries on 5xx/network errors.

    Transparently solves the anti-bot proof-of-work challenge if it's served.
    """
    delays = [5, 10, 20]
    for attempt in range(max_retries):
        try:
            response = SESSION.get(url, timeout=15)
            response.raise_for_status()
            # If we hit the interstitial, solve it and re-request. The marker
            # check is on raw bytes so the common case never decodes the body.
            for _ in range(MAX_CHALLENGE_SOLVES):
                if CHALLENGE_MARKER not in response.content:
                    break
                _solve_challenge(url, response.text)
                response = SESSION.get(url, timeout=15)
                response.raise_for_status()
            return response
        except requests.exceptions.HTTPError as e:
            if e.response is not None and e.response.status_code < 500:
                raise  # 4xx is permanent — don't retry
            if attempt == max_retries - 1:
                raise
            print(f"\n  [{attempt + 1}/{max_retries}] {e} — retrying in {delays[attempt]}s")
            time.sleep(delays[attempt])
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            if attempt == max_retries - 1:
                raise
            print(f"\n  [{attempt + 1}/{max_retries}] {e} — retrying in {delays[attempt]}s")
            time.sleep(delays[attempt])
    raise RuntimeError(f"fetch_with_retry: no attempts made (max_retries={max_retries})")


def main() -> None:
    # Load already-scraped events so we can skip them
    known_events: set[str] = set()
    existing_df: pd.DataFrame | None = None

    if not FULL_RESCRAPE and os.path.exists(OUTPUT_FILE):
        existing_df = pd.read_csv(OUTPUT_FILE)
        known_events = set(existing_df["event"].unique())
        print(f"Loaded {len(known_events)} existing events from {OUTPUT_FILE}")
    elif FULL_RESCRAPE:
        print("Full rescrape requested — ignoring existing data")

    all_events = []
    page_number = 1
    has_more_pages = True

    # Fetch the list of all events
    print("Fetching event list...")
    with tqdm(unit=" pages") as pbar:
        while has_more_pages:
            soup = BeautifulSoup(fetch_with_retry(BASE_URL + str(page_number)).content, "html.parser")
            event_list = soup.find_all("a", class_="b-link b-link_style_black")

            if not event_list:
                has_more_pages = False
            else:
                for event in event_list:
                    event_name = event.text.strip()
                    event_url = event["href"]

                    if event_name in known_events:
                        # Events are listed newest-first; hitting a known event
                        # means everything from here on is already scraped.
                        has_more_pages = False
                        break

                    all_events.append({"event_name": event_name, "event_url": event_url})

                if has_more_pages:
                    page_number += 1
                    pbar.update(1)
                    time.sleep(1)

    if not all_events:
        print("No new events found. Data is already up to date.")
        sys.exit(0)

    # Scrape the new events
    print(f"\nScraping {len(all_events)} new event(s)...")
    new_fights = []
    failed_events = []

    for event in tqdm(all_events, unit=" events"):
        event_name = event["event_name"]
        event_url = event["event_url"]

        try:
            event_response = fetch_with_retry(event_url)
            event_soup = BeautifulSoup(event_response.content, "html.parser")
        except Exception as e:
            print(f"\nGiving up on {event_name}: {e}")
            failed_events.append({"event_name": event_name, "event_url": event_url})
            time.sleep(1)
            continue

        # Iterate all tbodies — some event pages split main card and prelims
        # into separate sections, each with its own tbody.
        seen = set()
        for tbody in event_soup.find_all("tbody"):
            for fight_row in tbody.find_all("tr"):
                fight_data = fight_row.find_all("td")

                if len(fight_data) < 10:
                    continue
                try:
                    f1 = fight_data[1].find_all("p")[0].text.strip()
                    f2 = fight_data[1].find_all("p")[1].text.strip()

                    if (f1, f2) in seen:
                        continue

                    seen.add((f1, f2))
                    new_fights.append({
                        "event": event_name,
                        "fighter_1": f1,
                        "fighter_2": f2,
                        "result": fight_data[0].text.strip(),
                        "weight": fight_data[6].text.strip(),
                        "method": fight_data[7].text.strip(),
                        "round": fight_data[8].text.strip(),
                        "time": fight_data[9].text.strip(),
                    })
                except (IndexError, AttributeError):
                    continue

        time.sleep(1)

    # Prepend new fights to existing data (newest-first order)
    new_df = pd.DataFrame(new_fights)
    if new_df.empty:
        print("No fights collected. Check network or site structure.")
        sys.exit(1)
    elif existing_df is not None:
        combined = pd.concat([new_df, existing_df], ignore_index=True)
    else:
        combined = new_df

    combined.to_csv(OUTPUT_FILE, index=False)
    print(f"\nDone. Added {len(new_fights)} fights from {len(all_events) - len(failed_events)} event(s).")
    print(f"Total fights in dataset: {len(combined)}")

    if failed_events:
        with open(FAILED_LOG, "w") as f:
            for ev in failed_events:
                f.write(f"{ev['event_name']}\t{ev['event_url']}\n")
        print(f"\n{len(failed_events)} event(s) failed after all retries — logged to {FAILED_LOG}")
        print("Run the scraper again (incremental) to retry them automatically.")
    elif os.path.exists(FAILED_LOG):
        os.remove(FAILED_LOG)


if __name__ == "__main__":
    main()
