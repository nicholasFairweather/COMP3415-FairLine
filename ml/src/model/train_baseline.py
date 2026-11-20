import json 
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss

from src.model.elo import compute_elo

MODEL_VERSION = "elo_logreg_v1"
FEATURES = ["elo_diff"]
WARMUP_SEASONS = 1
DEFAULT_TEST_START = 2024
MODELS_DIR = Path(__file__).resolve().parents[2] / "models"

def load_training_frame(games: pd.DataFrame) -> pd.DataFrame:

    feats, _ = compute_elo(games)
    first_season = feats["season"].min()
    keep = feats["home_win"].notna() & (feats["season"] >= first_season + WARMUP_SEASONS)
    return feats[keep].reset_index(drop=True)


def split_by_season(df: pd.DataFrame, test_start: int) -> tuple[pd.DataFrame, pd.DataFrame]:

    train = df[df["season"] < test_start]
    test = df[df["season"] >= test_start]
    if train.empty or test.empty:
        raise ValueError(
            f"Split at {test_start} leaves an empty set "
            f"(seasons available: {int(df['season'].min())}-{int(df['season'].max())})"
        )
    return train, test


def evaluate(y_true, p) -> dict:

    y = np.asarray(y_true).astype(int)
    p = np.clip(np.asarray(p, dtype=float), 1e-6, 1 - 1e-6)
    return{
        "log_loss": float(log_loss(y, p, labels=[0, 1])),
        "brier": float(brier_score_loss(y, p)),
        "accuracy": float(accuracy_score(y, p > 0.5)),
        "n": int(len(y)),
    }

def fit_model(train: pd.DataFrame) -> LogisticRegression: 

    model = LogisticRegression()
    model.fit(train[FEATURES], train["home_win"].astype(int))
    return model

def predict_home_win_prob(model: LogisticRegression, df: pd.DataFrame) -> np.ndarray:
    return model.predict_proba(df[FEATURES])[:, 1]

def reliability_table(y_true, p) -> pd.DataFrame:
    """Predicted vs actual win rate in probability buckets (a calibration check)."""
    d = pd.DataFrame({"p": np.asarray(p, dtype=float), "y": np.asarray(y_true, dtype=float)})
    d["bucket"] = pd.cut(d["p"], [0, 0.3, 0.4, 0.5, 0.6, 0.7, 1.0])
    return d.groupby("bucket", observed=True).agg(
        games=("y", "size"), predicted=("p", "mean"), actual=("y", "mean")
    ).round(3)


def main(test_start: int = DEFAULT_TEST_START) -> None:
    from sqlalchemy import text

    from src.db import engine

    games = pd.read_sql(
        text(
            "SELECT game_id, season, week, home_team, away_team, "
            "home_team_score, away_team_score, kickoff FROM games"
        ),
        engine,
    )
    frame = load_training_frame(games)
    train, test = split_by_season(frame, test_start)

    print(f"Train: seasons {int(train.season.min())}-{int(train.season.max())} ({len(train)} games)")
    print(f"Test:  seasons {int(test.season.min())}-{int(test.season.max())} ({len(test)} games)")

    model = fit_model(train)
    p_model = predict_home_win_prob(model, test)
    results = {
        "model (logreg on elo_diff)": evaluate(test["home_win"], p_model),
        "raw Elo probability": evaluate(test["home_win"], test["elo_prob"]),
        "always the home win rate": evaluate(
            test["home_win"], np.full(len(test), train["home_win"].mean())
        ),
    }

    print(f"\n{'':30}{'log loss':>10}{'brier':>9}{'accuracy':>10}")
    for name, m in results.items():
        print(f"{name:30}{m['log_loss']:>10.4f}{m['brier']:>9.4f}{m['accuracy']:>10.3f}")
    print("(lower is better for log loss and Brier; a coin flip scores 0.6931 / 0.2500)")

    acc = results["model (logreg on elo_diff)"]["accuracy"]
    if acc > 0.70:
        print("\nWARNING: accuracy this high usually means leakage. Check the features.")

    print("\nCalibration on the test set (predicted should be close to actual):")
    print(reliability_table(test["home_win"], p_model).to_string())

    # Re-fit on everything played so far and save for predict.py.
    final = fit_model(frame)
    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump(
        {"model": final, "features": FEATURES, "version": MODEL_VERSION},
        MODELS_DIR / "baseline.joblib",
    )
    with open(MODELS_DIR / "baseline_metrics.json", "w") as f:
        json.dump(
            {"version": MODEL_VERSION, "test_start": test_start, "results": results},
            f, indent=2,
        )
    print(f"\nSaved {MODELS_DIR / 'baseline.joblib'} and baseline_metrics.json")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_TEST_START)