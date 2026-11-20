import pandas as pd
import pytest

from src.model.elo import (
    HOME_ADVANTAGE,
    SEASON_CARRYOVER,
    START_RATING,
    compute_elo,
    expected_home_win_prob,
    margin_multiplier,
    update_ratings,
)


def make_games(rows):
    """rows: (game_id, season, kickoff, home, away, home_score, away_score)"""
    return pd.DataFrame(
        rows,
        columns=[
            "game_id", "season", "kickoff", "home_team", "away_team",
            "home_team_score", "away_team_score",
        ],
    ).assign(kickoff=lambda d: pd.to_datetime(d["kickoff"]))


# --- Probability and update maths ------------------------------------------

def test_equal_ratings_without_home_advantage_is_fifty_fifty():
    assert expected_home_win_prob(1500, 1500, home_advantage=0) == pytest.approx(0.5)


def test_home_advantage_favours_home_team():
    assert expected_home_win_prob(1500, 1500) > 0.5


def test_stronger_team_is_favoured():
    assert expected_home_win_prob(1700, 1500) > expected_home_win_prob(1500, 1500)


def test_update_is_zero_sum():
    new_h, new_a = update_ratings(1500, 1500, 27, 20)
    assert (new_h + new_a) == pytest.approx(3000.0)


def test_winner_gains_and_loser_drops():
    new_h, new_a = update_ratings(1500, 1500, 27, 20)
    assert new_h > 1500 > new_a


def test_upset_moves_ratings_more_than_expected_win():
    # Same 7-point margin; the underdog winning should swing ratings further.
    upset_h, _ = update_ratings(1400, 1600, 27, 20, home_advantage=0)
    expected_h, _ = update_ratings(1600, 1400, 27, 20, home_advantage=0)
    assert (upset_h - 1400) > (expected_h - 1600)


def test_bigger_margin_moves_ratings_more():
    small_h, _ = update_ratings(1500, 1500, 21, 20)
    big_h, _ = update_ratings(1500, 1500, 45, 10)
    assert (big_h - 1500) > (small_h - 1500)


def test_tie_has_neutral_multiplier():
    assert margin_multiplier(0, 0.0) == 1.0


# --- No-leakage behaviour (the important ones) -----------------------------

def test_first_game_uses_starting_ratings():
    games = make_games([(1, 2024, "2024-09-08", "KC", "BAL", 27, 20)])
    out, _ = compute_elo(games)
    assert out.loc[0, "home_elo"] == START_RATING
    assert out.loc[0, "away_elo"] == START_RATING


def test_a_games_own_result_does_not_change_its_own_features():
    low = make_games([(1, 2024, "2024-09-08", "KC", "BAL", 0, 40)])
    high = make_games([(1, 2024, "2024-09-08", "KC", "BAL", 40, 0)])
    out_low, _ = compute_elo(low)
    out_high, _ = compute_elo(high)
    assert out_low.loc[0, "elo_prob"] == out_high.loc[0, "elo_prob"]
    assert out_low.loc[0, "home_elo"] == out_high.loc[0, "home_elo"]


def test_second_game_sees_ratings_after_first_game_only():
    games = make_games([
        (1, 2024, "2024-09-08", "KC", "BAL", 27, 20),
        (2, 2024, "2024-09-15", "BAL", "KC", 17, 24),
    ])
    out, _ = compute_elo(games)
    exp_kc, exp_bal = update_ratings(1500, 1500, 27, 20)
    assert out.loc[1, "home_elo"] == pytest.approx(exp_bal)   # BAL is home in game 2
    assert out.loc[1, "away_elo"] == pytest.approx(exp_kc)


def test_changing_a_future_result_never_changes_an_earlier_feature():
    base = [
        (1, 2024, "2024-09-08", "KC", "BAL", 27, 20),
        (2, 2024, "2024-09-15", "BAL", "KC", 17, 24),
    ]
    altered = [base[0], (2, 2024, "2024-09-15", "BAL", "KC", 3, 45)]
    out_a, _ = compute_elo(make_games(base))
    out_b, _ = compute_elo(make_games(altered))
    assert out_a.loc[0, "elo_prob"] == out_b.loc[0, "elo_prob"]
    assert out_a.loc[1, "elo_prob"] == out_b.loc[1, "elo_prob"]  # game 2 features also pre-game


def test_unplayed_games_do_not_change_ratings():
    games = make_games([
        (1, 2024, "2024-09-08", "KC", "BAL", 27, 20),
        (2, 2024, "2024-09-15", "KC", "BAL", None, None),   # not played yet
        (3, 2024, "2024-09-22", "KC", "BAL", None, None),
    ])
    out, _ = compute_elo(games)
    assert out.loc[1, "home_elo"] == pytest.approx(out.loc[2, "home_elo"])
    assert out.loc[1, "away_elo"] == pytest.approx(out.loc[2, "away_elo"])


def test_games_are_processed_in_kickoff_order_not_row_order():
    ordered = make_games([
        (1, 2024, "2024-09-08", "KC", "BAL", 27, 20),
        (2, 2024, "2024-09-15", "BAL", "KC", 17, 24),
    ])
    shuffled = ordered.iloc[::-1].reset_index(drop=True)
    out_a, _ = compute_elo(ordered)
    out_b, _ = compute_elo(shuffled)
    assert out_a["elo_prob"].tolist() == out_b["elo_prob"].tolist()


# --- Season carry-over and labels ------------------------------------------

def test_ratings_regress_toward_mean_between_seasons():
    games = make_games([
        (1, 2023, "2023-12-31", "KC", "BAL", 30, 10),
        (2, 2024, "2024-09-08", "KC", "BAL", 20, 17),
    ])
    out, _ = compute_elo(games)
    new_kc, _ = update_ratings(1500, 1500, 30, 10)
    expected = START_RATING + (new_kc - START_RATING) * SEASON_CARRYOVER
    assert out.loc[1, "home_elo"] == pytest.approx(expected)


def test_home_win_label():
    games = make_games([
        (1, 2024, "2024-09-08", "KC", "BAL", 27, 20),
        (2, 2024, "2024-09-09", "BUF", "MIA", 10, 17),
        (3, 2024, "2024-09-10", "NYJ", "NE", 17, 17),       # tie
        (4, 2024, "2024-09-11", "DAL", "PHI", None, None),  # unplayed
    ])
    out, _ = compute_elo(games)
    assert out.loc[0, "home_win"] == 1.0
    assert out.loc[1, "home_win"] == 0.0
    assert pd.isna(out.loc[2, "home_win"])
    assert pd.isna(out.loc[3, "home_win"])


def test_elo_prob_reflects_home_advantage_for_new_teams():
    games = make_games([(1, 2024, "2024-09-08", "KC", "BAL", None, None)])
    out, _ = compute_elo(games)
    assert out.loc[0, "elo_prob"] == pytest.approx(
        expected_home_win_prob(START_RATING, START_RATING, HOME_ADVANTAGE)
    )