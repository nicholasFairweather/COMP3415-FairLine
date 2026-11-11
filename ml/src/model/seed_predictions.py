from sqlalchemy import text
 
from src.db import engine
 
MODEL_VERSION = "seed"
 
# Home win probability between 0.30 and 0.70, derived from game_id.
SEED_SQL = """
INSERT INTO predictions (game_id, home_win_prob, model_version)
SELECT
    game_id,
    ROUND((0.30 + 0.40 * ((game_id * 37) % 100) / 100.0)::numeric, 4),
    :version
FROM games
ON CONFLICT (game_id, model_version)
DO UPDATE SET
    home_win_prob = EXCLUDED.home_win_prob,
    created_at = NOW()
"""
 
 
def main() -> None:
    with engine.begin() as conn:
        conn.execute(text(SEED_SQL), {"version": MODEL_VERSION})
 
    with engine.connect() as conn:
        count = conn.execute(
            text("SELECT COUNT(*) FROM predictions WHERE model_version = :v"),
            {"v": MODEL_VERSION},
        ).scalar()
        sample = conn.execute(
            text(
                """
                SELECT g.season, g.week, g.home_team, g.away_team, p.home_win_prob
                FROM predictions p
                JOIN games g ON g.game_id = p.game_id
                WHERE p.model_version = :v
                ORDER BY g.kickoff DESC
                LIMIT 5
                """
            ),
            {"v": MODEL_VERSION},
        ).all()
 
    print(f"Seed predictions in database: {count}")
    print("Most recent games:")
    for season, week, home, away, prob in sample:
        print(f"  {season} wk{week}  {home} vs {away}: home win prob {prob}")
 
 
if __name__ == "__main__":
    main()
 