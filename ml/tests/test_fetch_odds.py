from datetime import datetime, timezone

from src.ingest.fetch_odds import parse_events, team_names


def event(home="Detroit Lions", away="Green Bay Packers", bookmakers=None):
    return {
        "id": "abc123",
        "sport_key": "americanfootball_nfl",
        "commence_time": "2026-11-29T18:00:00Z",
        "home_team": home,
        "away_team": away,
        "bookmakers": bookmakers if bookmakers is not None else [
            {
                "key": "draftkings",
                "title": "DraftKings",
                "last_update": "2026-11-18T15:00:00Z",
                "markets": [
                    {
                        "key": "h2h",
                        "outcomes": [
                            {"name": "Green Bay Packers", "price": 130},
                            {"name": "Detroit Lions", "price": -150},
                        ],
                    }
                ],
            }
        ],
    }


def test_parses_one_row_per_bookmaker():
    rows = parse_events([event()])
    assert len(rows) == 1
    row = rows[0]
    assert row["bookmaker"] == "draftkings"
    assert row["home_odds"] == -150  # matched by name, not by position in the list
    assert row["away_odds"] == 130
    assert row["commence_time"] == datetime(2026, 11, 29, 18, 0, tzinfo=timezone.utc)
    assert row["fetched_at"] == datetime(2026, 11, 18, 15, 0, tzinfo=timezone.utc)


def test_skips_unknown_teams():
    assert parse_events([event(home="Toronto Argonauts")]) == []


def test_skips_bookmaker_without_moneyline():
    books = [{"key": "fanduel", "last_update": "2026-11-18T15:00:00Z",
              "markets": [{"key": "spreads", "outcomes": []}]}]
    assert parse_events([event(bookmakers=books)]) == []


def test_skips_bookmaker_missing_a_price():
    books = [{"key": "fanduel", "last_update": "2026-11-18T15:00:00Z",
              "markets": [{"key": "h2h", "outcomes": [{"name": "Detroit Lions", "price": -150}]}]}]
    assert parse_events([event(bookmakers=books)]) == []


def test_event_with_no_bookmakers_gives_no_rows():
    assert parse_events([event(bookmakers=[])]) == []


def test_team_names_covers_abbreviation_and_full_name():
    assert team_names("Detroit Lions") == ["DET", "Detroit Lions"]
    assert team_names("Los Angeles Rams") == ["LA", "Los Angeles Rams"]