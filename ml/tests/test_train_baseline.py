import random

import numpy as np
import pandas as pd
import pytest

from src.model.train_baseline import (
    FEATURES,
    evaluate,
    fit_model,
    load_training_frame,
    predict_home_win_prob,
    reliability_table,
    split_by_season,
)


def synthetic_league(seasons=range(2015, 2025), seed=1):
    """A fake league with known team strengths, so the model has real signal to find."""
    rng = random.Random(seed)
    teams = [f"T{i}" for i in range(32)]
    strength = {t: rng.gauss(0, 5) for t in teams}
    rows, gid = [], 0
    for season in seasons:
        for week in range(17):
            order = teams[:]
            rng.shuffle(order)
            for i in range(0, 32, 2):
                h, a = order[i], order[i + 1]
                margin = strength[h] - strength[a] + 2.5 + rng.gauss(0, 13)
                gid += 1
                rows.append((
                    gid, season,
                    pd.Timestamp(season, 9, 1) + pd.Timedelta(days=7 * week),
                    h, a,
                    max(0, round(24 + margin / 2)), max(0, round(24 - margin / 2)),
                ))
    return pd.DataFrame(rows, columns=[
        "game_id", "season", "kickoff", "home_team", "away_team",
        "home_team_score", "away_team_score",
    ])


@pytest.fixture(scope="module")
def frame():
    return load_training_frame(synthetic_league())


# --- Leakage guards --------------------------------------------------------

def test_features_use_only_pre_game_columns():
    for col in FEATURES:
        assert "score" not in col
        assert col != "home_win"


def test_training_frame_drops_warmup_season(frame):
    assert frame["season"].min() == 2016      # 2015 was the warm-up


def test_training_frame_has_no_unplayed_or_tied_games(frame):
    assert frame["home_win"].notna().all()


def test_split_never_trains_on_the_future(frame):
    train, test = split_by_season(frame, 2022)
    assert train["season"].max() < test["season"].min()
    assert set(train["game_id"]).isdisjoint(set(test["game_id"]))
    assert len(train) + len(test) == len(frame)


def test_split_rejects_an_empty_side(frame):
    with pytest.raises(ValueError):
        split_by_season(frame, 2099)
    with pytest.raises(ValueError):
        split_by_season(frame, 2000)


# --- Metrics ---------------------------------------------------------------

def test_coin_flip_scores_match_known_values():
    y = np.array([1, 0, 1, 0, 1, 0, 1, 0])
    m = evaluate(y, np.full(8, 0.5))
    assert m["log_loss"] == pytest.approx(0.693147, abs=1e-5)
    assert m["brier"] == pytest.approx(0.25)


def test_confident_correct_predictions_score_better_than_coin_flip():
    y = np.array([1, 0, 1, 0])
    good = evaluate(y, np.array([0.9, 0.1, 0.9, 0.1]))
    assert good["log_loss"] < 0.6931
    assert good["brier"] < 0.25
    assert good["accuracy"] == 1.0


def test_confident_wrong_predictions_are_punished():
    y = np.array([1, 0, 1, 0])
    bad = evaluate(y, np.array([0.1, 0.9, 0.1, 0.9]))
    assert bad["log_loss"] > 0.6931
    assert bad["accuracy"] == 0.0


def test_evaluate_survives_probabilities_of_exactly_0_and_1():
    m = evaluate(np.array([1, 0]), np.array([1.0, 0.0]))
    assert np.isfinite(m["log_loss"])


# --- The model itself ------------------------------------------------------

def test_model_learns_that_a_higher_home_rating_means_a_higher_win_chance(frame):
    train, _ = split_by_season(frame, 2022)
    model = fit_model(train)
    assert model.coef_[0][0] > 0


def test_probabilities_are_valid(frame):
    train, test = split_by_season(frame, 2022)
    p = predict_home_win_prob(fit_model(train), test)
    assert len(p) == len(test)
    assert ((p > 0) & (p < 1)).all()


def test_model_beats_a_coin_flip_on_held_out_seasons(frame):
    train, test = split_by_season(frame, 2022)
    p = predict_home_win_prob(fit_model(train), test)
    m = evaluate(test["home_win"], p)
    assert m["log_loss"] < 0.6931
    assert m["accuracy"] > 0.55


def test_model_beats_always_guessing_the_home_win_rate(frame):
    train, test = split_by_season(frame, 2022)
    p = predict_home_win_prob(fit_model(train), test)
    model_ll = evaluate(test["home_win"], p)["log_loss"]
    base_ll = evaluate(test["home_win"], np.full(len(test), train["home_win"].mean()))["log_loss"]
    assert model_ll < base_ll


def test_reliability_table_buckets_cover_all_games(frame):
    train, test = split_by_season(frame, 2022)
    p = predict_home_win_prob(fit_model(train), test)
    table = reliability_table(test["home_win"], p)
    assert table["games"].sum() == len(test)
    assert ((table["actual"] >= 0) & (table["actual"] <= 1)).all()