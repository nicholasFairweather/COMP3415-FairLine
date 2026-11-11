import pytest

from src.betting.odds_math import (
    american_to_decimal,
    american_to_prob,
    edge,
    expected_value,
    kelly_fraction,
    no_vig_probs,
    suggested_stake,
)


# Odds conversion tests
def test_decimal_negative_odds():
    # -110 -> 1 + 100/110
    assert american_to_decimal(-110) == pytest.approx(1.909091, abs=1e-6)


def test_decimal_positive_odds():
    assert american_to_decimal(150) == pytest.approx(2.5)


def test_implied_probability_negative_odds():
    assert american_to_prob(-110) == pytest.approx(0.5238095, abs=1e-6)


def test_implied_probability_positive_odds():
    assert american_to_prob(150) == pytest.approx(0.40)


def test_implied_prob_even_money():
    assert american_to_prob(100) == pytest.approx(0.5)
    assert american_to_prob(-100) == pytest.approx(0.5)


@pytest.mark.parametrize("bad", [0, 50, -50, 99, -99])
def test_invalid_odds_rejected(bad):
    with pytest.raises(ValueError):
        american_to_prob(bad)


# No-vig probability tests
def test_no_vig_symmetric_market():
    # Equal odds on both sides must give 50/50 after removing the vig
    home, away = no_vig_probs(-110, -110)
    assert home == pytest.approx(0.5)
    assert away == pytest.approx(0.5)


def test_no_vig_favourite_and_underdog():
    # implied 0.6 and 0.434783, total 1.034783
    home, away = no_vig_probs(-150, 130)
    assert home == pytest.approx(0.579832, abs=1e-6)
    assert away == pytest.approx(0.420168, abs=1e-6)


def test_no_vig_probs_sum_to_one():
    home, away = no_vig_probs(-275, 225)
    assert home + away == pytest.approx(1.0)


# Edge tests
def test_edge_positive():
    assert edge(0.60, 0.55) == pytest.approx(0.05)


def test_edge_negative():
    assert edge(0.45, 0.50) == pytest.approx(-0.05)


def test_edge_rejects_bad_probability():
    with pytest.raises(ValueError):
        edge(1.2, 0.5)


# Expected value tests
def test_ev_positive():
    # profit on 100 at -110 = 90.909; 0.55*90.909 - 0.45*100 = 5.0
    assert expected_value(0.55, -110, stake=100) == pytest.approx(5.0)


def test_ev_negative_at_fair_coin_with_vig():
    # A 50% chance at -110 loses money on average
    assert expected_value(0.50, -110, stake=100) < 0


def test_ev_zero_when_probability_matches_odds():
    p = american_to_prob(150)
    assert expected_value(p, 150, stake=100) == pytest.approx(0.0, abs=1e-9)


# Kelly fraction tests
def test_kelly_full():
    # b = 0.90909, p = 0.55 -> (0.5 - 0.45) / 0.90909 = 0.055
    assert kelly_fraction(0.55, -110) == pytest.approx(0.055)


def test_kelly_fractional():
    assert kelly_fraction(0.55, -110, fraction=0.5) == pytest.approx(0.0275)


def test_kelly_never_negative():
    assert kelly_fraction(0.50, -110) == 0.0
    assert kelly_fraction(0.30, -110) == 0.0


def test_kelly_rejects_bad_fraction():
    with pytest.raises(ValueError):
        kelly_fraction(0.55, -110, fraction=0)
    with pytest.raises(ValueError):
        kelly_fraction(0.55, -110, fraction=1.5)


# Suggested stake tests
def test_suggested_stake_moderate():
    # 1000 * 0.055 * 0.5 = 27.50
    assert suggested_stake(1000, 0.55, -110, "moderate") == pytest.approx(27.50)


def test_suggested_stake_conservative_is_smaller_than_aggressive():
    low = suggested_stake(1000, 0.55, -110, "conservative")
    high = suggested_stake(1000, 0.55, -110, "aggressive")
    assert 0 < low < high


def test_suggested_stake_no_edge_is_zero():
    assert suggested_stake(1000, 0.50, -110, "moderate") == 0.0


@pytest.mark.parametrize("bankroll", [0, -100])
def test_suggested_stake_rejects_bad_bankroll(bankroll):
    with pytest.raises(ValueError, match="greater than 0"):
        suggested_stake(bankroll, 0.55, -110)


def test_suggested_stake_rejects_unknown_risk():
    with pytest.raises(ValueError):
        suggested_stake(1000, 0.55, -110, "yolo")