import sys 

import pandas as pd

from src.teams import normalize_abbr, to_full_name

# Flag to determine whether to use full team names or abbreviations in the output
USE_FULL_NAMES = False

# Default values to load if none are specified
DEFAULT_SEASONS = [2021, 2022, 2023, 2024, 2025, 2026]
DEFAULT_KICKOFF_TIME = "13:00"
KICKOFF_TZ = "America/New_York"


def transform_schedule(raw: pd.DataFrame, use_full_names: bool = USE_FULL_NAMES) -> pd.DataFrame:

    df = raw[raw["game_type"] == "REG"].copy()

    def team(abbr: str) -> str:
        abbr = normalize_abbr(abbr)
        return to_full_name(abbr) if use_full_names else abbr

    gametime = df["gametime"].fillna(DEFAULT_KICKOFF_TIME)
    df["kickoff"] = pd.to_datetime(df["gameday"].astype(str) + " " + gametime.astype(str)).dt.tz_localize(KICKOFF_TZ)

    out = pd.DataFrame(
         {
            "season": df["season"].astype(int),
            "week": df["week"].astype(int),
            "home_team": df["home_team"].map(team),
            "away_team": df["away_team"].map(team),
            "home_team_score": df["home_score"],
            "away_team_score": df["away_score"],
            "kickoff": df["kickoff"],
        }
    )

    out = out.astype({"home_team_score": "Int64", "away_team_score": "Int64"})
    return out.reset_index(drop=True)

UPSERT_SQL = """
INSERT INTO games (season, week, home_team, away_team, home_team_score, away_team_score, kickoff)
VALUES (:season, :week, :home_team, :away_team, :home_team_score, :away_team_score, :kickoff)
ON CONFLICT (week, home_team, away_team, season)
DO UPDATE SET
    home_team_score = EXCLUDED.home_team_score,
    away_team_score = EXCLUDED.away_team_score,
    kickoff = EXCLUDED.kickoff
"""    

def to_records(games: pd.DataFrame) -> list[dict]:
    records = []
    for row in games.to_dict(orient="records"):
        clean = {k: (None if pd.isna(v) else v) for k, v in row.items()}
        clean["kickoff"] = clean["kickoff"].to_pydatetime()
        for key in ("home_team_score", "away_team_score"):
            if clean[key] is not None:
                clean[key] = int(clean[key])
        records.append(clean)
    return records


def main(seasons: list[int]) -> None:

    import nflreadpy as nfl
    from sqlalchemy import text

    from src.db import engine

    print(f"Downloading schedules for seasons: {seasons}")
    raw = nfl.load_schedules(seasons).to_pandas()
    games = transform_schedule(raw)
    print(f"Prepared {len(games)} regular-season games")
 
    with engine.begin() as conn:  # one transaction: all rows or none
        conn.execute(text(UPSERT_SQL), to_records(games))
 
    print("Done. Rows per season now in the database:")
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT season, COUNT(*) FROM games GROUP BY season ORDER BY season")
        ).all()
    for season, count in rows:
        print(f"  {season}: {count}")
 
 
if __name__ == "__main__":
    args = [int(a) for a in sys.argv[1:]]
    main(args or DEFAULT_SEASONS)