import numpy as np
import pandas as pd
import pytest

from src.model.elo import compute_elo
from src.model.predict import build_prediction_rows, is_unplayed, load_model
from src.model.train_baseline import (
    FEATURES,
    MODEL_VERSION,
    fit_model,
    load_training_frame,
)
from test_train_baseline import synthetic_league


@pytest.fixture(scope="module")
def setup():
    """Synthetic league where the final week has not been played yet."""
    games = synthetic_league(seasons=range(2015, 2023))
    last_week = games["kickoff"] == games["kickoff"].max()
    games.loc[last_week, ["home_team_score", "away_team_score"]] = np.nan

    train = load_training_frame(games)
    bundle = {"model": fit_model(train), "features": FEATURES, "version": MODEL_VERSION}
    feats, _ = compute_elo(games)
    return feats, bundle, int(last_week.sum())


def test_every_game_gets_one_row(setup):
    feats, bundle, _ = setup
    rows = build_prediction_rows(feats, bundle)
    assert len(rows) == len(feats)
    assert len({r["game_id"] for r in rows}) == len(feats)


def test_upcoming_only_returns_just_the_unplayed_games(setup):
    feats, bundle, n_unplayed = setup
    rows = build_prediction_rows(feats, bundle, upcoming_only=True)
    assert len(rows) == n_unplayed
    unplayed_ids = set(feats.loc[is_unplayed(feats), "game_id"])
    assert {r["game_id"] for r in rows} == unplayed_ids


def test_probabilities_are_valid_and_rounded_to_four_places(setup):
    feats, bundle, _ = setup
    for r in build_prediction_rows(feats, bundle):
        p = r["home_win_prob"]
        assert 0.0 <= p <= 1.0
        assert p == round(p, 4)


def test_rows_use_plain_python_types_the_database_can_store(setup):
    feats, bundle, _ = setup
    r = build_prediction_rows(feats, bundle)[0]
    assert type(r["game_id"]) is int
    assert type(r["home_win_prob"]) is float
    assert type(r["model_version"]) is str


def test_rows_are_tagged_with_the_model_version_and_never_as_seed(setup):
    feats, bundle, _ = setup
    versions = {r["model_version"] for r in build_prediction_rows(feats, bundle)}
    assert versions == {MODEL_VERSION}
    assert "seed" not in versions


def test_higher_home_rating_gives_a_higher_probability(setup):
    feats, bundle, _ = setup
    rows = build_prediction_rows(feats, bundle)
    prob = {r["game_id"]: r["home_win_prob"] for r in rows}
    ordered = feats.sort_values("elo_diff")
    low, high = ordered.iloc[0], ordered.iloc[-1]
    assert prob[int(high["game_id"])] > prob[int(low["game_id"])]


def test_no_games_means_no_rows(setup):
    feats, bundle, _ = setup
    played_only = feats[~is_unplayed(feats)]
    assert build_prediction_rows(played_only, bundle, upcoming_only=True) == []


def test_missing_model_file_gives_a_helpful_error(tmp_path):
    with pytest.raises(FileNotFoundError, match="train_baseline"):
        load_model(tmp_path / "nope.joblib")