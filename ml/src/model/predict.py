import sys


import joblib
import pandas as pd

from src.model.elo import compute_elo
from src.model.train_baseline import MODELS_DIR

MODEL_PATH = MODELS_DIR / "baseline.joblib"

UPSERT_SQL = """
INSERT INTO predictions (game_id, home_win_prob, model_version)
VALUES (:game_id, :home_win_prob, :model_version)
ON CONFLICT (game_id, model_version)
DO UPDATE SET
    home_win_prob = EXCLUDED.home_win_prob,
    created_at = NOW()
"""


def load_model(path=MODEL_PATH) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"No saved model at {path}. Run: python -m src.model.train_baseline"
        )
    return joblib.load(path)


def is_unplayed(feats: pd.DataFrame) -> pd.Series:
    return feats["home_team_score"].isna() | feats["away_team_score"].isna()


def build_prediction_rows(feats: pd.DataFrame, bundle: dict, upcoming_only: bool = False) -> list[dict]:

    df = feats[is_unplayed(feats)] if upcoming_only else feats
    if df.empty:
        return []
    probs = bundle["model"].predict_proba(df[bundle["features"]])[:, 1]

    return[
        {
            "game_id": int(game_id),
            "home_win_prob": round(float(p), 4),
            "model_version": bundle["version"],
        }
        for game_id, p in zip(df["game_id"], probs)
    ]


def main(upcoming_only: bool = False) -> None:
    from sqlalchemy import text

    from src.db import engine

    bundle = load_model()
    games = pd.read_sql(
        text(
            "SELECT game_id, season, week, home_team, away_team, "
            "home_team_score, away_team_score, kickoff FROM games"
        ),
        engine,
    )
    feats, _ = compute_elo(games)
    rows = build_prediction_rows(feats, bundle, upcoming_only)

    if not rows:
        print("No games to predict.")
        return

    with engine.begin() as conn:  # one transaction: all rows or none
        conn.execute(text(UPSERT_SQL), rows)

    scope = "upcoming games" if upcoming_only else "all games"
    print(f"Wrote {len(rows)} predictions ({scope}) as model_version '{bundle['version']}'")

    with engine.connect() as conn:
        counts = conn.execute(
            text(
                "SELECT model_version, COUNT(*) FROM predictions "
                "GROUP BY model_version ORDER BY model_version"
            )
        ).all()
    print("Predictions per model version in the database:")
    for version, n in counts:
        print(f"  {version}: {n}")

    prob = {r["game_id"]: r["home_win_prob"] for r in rows}
    upcoming = feats[is_unplayed(feats) & feats["game_id"].isin(prob)]
    upcoming = upcoming.sort_values("kickoff").head(5)
    if len(upcoming):
        print("\nNext games:")
        for g in upcoming.itertuples():
            print(
                f"  {g.season} wk{g.week}  {g.home_team} vs {g.away_team}: "
                f"home win prob {prob[g.game_id]:.3f}  (Elo {g.home_elo:.0f} v {g.away_elo:.0f})"
            )


if __name__ == "__main__":
    main(upcoming_only="--upcoming" in sys.argv[1:])