# Fraction of full Kelly used for each risk setting
RISK_FRACTION = {
    "conservative": 0.25,
    "moderate": 0.5,
    "aggressive": 1,
}


# Checks for valid odds values
def check_odds(odds: float) -> None:
    if odds == 0 or -100 < odds < 100:
        raise ValueError(f"Invalid odds value: {odds}. Odds must be 100 or greater, or -100 or less.")


# Checks for valid probability values
def check_prob(prob: float) -> None:
    if prob < 0.0 or prob > 1.0:
        raise ValueError(f"Invalid probability value: {prob}. Probability must be between 0.0 and 1.0.")


# Converts American odds to decimal odds
def american_to_decimal(odds: float) -> float:
    check_odds(odds)
    if odds > 0:
        return (odds / 100) + 1
    else:
        return (100 / abs(odds)) + 1


# Converts American odds to implied probability (includes the bookmaker's margin)
def american_to_prob(odds: float) -> float:
    check_odds(odds)
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return abs(odds) / (abs(odds) + 100)


# Calculates the no-vig probabilities for home and away teams based on their American odds
def no_vig_probs(home_odds: float, away_odds: float) -> tuple[float, float]:
    p_home = american_to_prob(home_odds)
    p_away = american_to_prob(away_odds)
    total_prob = p_home + p_away
    return p_home / total_prob, p_away / total_prob


# Calculates the edge of a bet: model probability minus the fair (no-vig) probability
def edge(model_prob: float, fair_prob: float) -> float:
    check_prob(model_prob)
    check_prob(fair_prob)
    return model_prob - fair_prob


# Calculates the expected profit of a bet: p * profit - (1 - p) * stake
def expected_value(model_prob: float, odds: float, stake: float = 1.0) -> float:
    check_prob(model_prob)
    profit = stake * (american_to_decimal(odds) - 1)
    return model_prob * profit - (1 - model_prob) * stake


# Calculates the fraction of the bankroll to stake: (b*p - q) / b, scaled by fraction
# Returns 0.0 when there is no positive edge (never a negative stake)
def kelly_fraction(model_prob: float, odds: float, fraction: float = 1.0) -> float:
    check_prob(model_prob)
    if not (0.0 < fraction <= 1.0):
        raise ValueError(f"Invalid fraction value: {fraction}. Fraction must be greater than 0.0 and at most 1.0.")
    b = american_to_decimal(odds) - 1
    q = 1 - model_prob
    full_kelly = (b * model_prob - q) / b
    return max(0.0, full_kelly) * fraction


# Calculates the suggested stake based on the bankroll, model's probability, odds, and risk level
def suggested_stake(bankroll: float, model_prob: float, odds: float, risk: str = "moderate") -> float:
    if bankroll <= 0:
        raise ValueError(f"Invalid bankroll value: {bankroll}. Bankroll must be greater than 0.")
    if risk not in RISK_FRACTION:
        raise ValueError(f"Invalid risk value: {risk}. Risk must be one of {list(RISK_FRACTION.keys())}.")
    return round(bankroll * kelly_fraction(model_prob, odds, RISK_FRACTION[risk]), 2)