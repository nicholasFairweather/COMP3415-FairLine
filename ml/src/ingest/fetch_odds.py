"""Fetch current NFL moneyline odds from The Odds API and store them in the odds table.

Usage (from the ml/ folder, with the virtual environment active):
    python -m src.ingest.fetch_odds                         # calls the API (uses 1 credit)
    python -m src.ingest.fetch_odds --from-file data/x.json # reuse a saved response (free)

Every API response is saved to ml/data/ so it can be replayed with --from-file
while developing, instead of spending the free monthly quota.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.teams import ABBR_TO_FULL, FULL_TO_ABBR

ODDS_URL = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/odds"
ML_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = ML_DIR / "data"

# A game in the database matches an API event if the kickoff is within this window
MATCH_WINDOW = timedelta(days=1)


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def parse_events(events: list[dict]) -> list[dict]:
    rows = []
    for event in events:
        home, away = event.get("home_team"), event.get("away_team")
        if home not in FULL_TO_ABBR or away not in FULL_TO_ABBR:
            continue

        for book in event.get("bookmakers", []):
            market = next((m for m in book.get("markets", []) if m.get("key") == "h2h"), None)
            if market is None:
                continue

            prices = {o.get("name"): o.get("price") for o in market.get("outcomes", [])}
            if prices.get(home) is None or prices.get(away) is None:
                continue

            rows.append({
                "home_team": home,
                "away_team": away,
                "commence_time": parse_time(event["commence_time"]),
                "bookmaker": book.get("key") or book.get("title"),
                "home_odds": int(round(prices[home])),
                "away_odds": int(round(prices[away])),
                "fetched_at": parse_time(book.get("last_update") or event["commence_time"]),
            })
    return rows


def team_names(full_name: str) -> list[str]:
    abbr = FULL_TO_ABBR[full_name]
    return [abbr, ABBR_TO_FULL[abbr]]


def call_api(api_key: str) -> list[dict]:
    import requests

    response = requests.get(
        ODDS_URL,
        params={
            "apiKey": api_key,
            "regions": "us",
            "markets": "h2h",
            "oddsFormat": "american",
            "dateFormat": "iso",
        },
        timeout=30,
    )
    if response.status_code != 200:
        raise RuntimeError(f"The Odds API returned HTTP {response.status_code}: {response.text[:300]}")

    print(f"API credits used: {response.headers.get('x-requests-used')}, "
          f"remaining: {response.headers.get('x-requests-remaining')}")
    return response.json()


def save_response(events: list[dict]) -> Path:
    DATA_DIR.mkdir(exist_ok=True)
    path = DATA_DIR / f"odds_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}.json"
    path.write_text(json.dumps(events, indent=2))
    return path


FIND_GAME_SQL = """
SELECT game_id FROM games
WHERE home_team = ANY(:home) AND away_team = ANY(:away)
  AND kickoff BETWEEN :start AND :end
ORDER BY ABS(EXTRACT(EPOCH FROM (kickoff - :kickoff)))
LIMIT 1
"""

INSERT_SQL = """
INSERT INTO odds (game_id, bookmaker, home_odds, away_odds, fetched_at)
VALUES (:game_id, :bookmaker, :home_odds, :away_odds, :fetched_at)
ON CONFLICT (game_id, bookmaker, fetched_at) DO NOTHING
"""


def main(argv: list[str]) -> None:
    from sqlalchemy import text

    from src.db import engine  # also loads ml/.env

    if "--from-file" in argv:
        path = Path(argv[argv.index("--from-file") + 1])
        events = json.loads(path.read_text())
        print(f"Loaded {len(events)} events from {path}")
    else:
        api_key = os.getenv("ODDS_API_KEY")
        if not api_key:
            raise RuntimeError("ODDS_API_KEY is not set in ml/.env")
        events = call_api(api_key)
        print(f"Fetched {len(events)} events. Saved response to {save_response(events)}")

    rows = parse_events(events)
    inserted, unmatched = 0, set()

    with engine.begin() as conn:  # one transaction: all rows or none
        for row in rows:
            game_id = conn.execute(text(FIND_GAME_SQL), {
                "home": team_names(row["home_team"]),
                "away": team_names(row["away_team"]),
                "kickoff": row["commence_time"],
                "start": row["commence_time"] - MATCH_WINDOW,
                "end": row["commence_time"] + MATCH_WINDOW,
            }).scalar()

            if game_id is None:
                unmatched.add(f"{row['away_team']} @ {row['home_team']} ({row['commence_time']:%Y-%m-%d})")
                continue

            result = conn.execute(text(INSERT_SQL), {**row, "game_id": game_id})
            inserted += result.rowcount

    print(f"Stored {inserted} new odds rows from {len(rows)} bookmaker prices.")
    if unmatched:
        print("No matching game in the database for (run load_games first?):")
        for name in sorted(unmatched):
            print(f"  {name}")


if __name__ == "__main__":
    main(sys.argv[1:])