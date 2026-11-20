import math 

import pandas as pd

START_RATING = 1500.0
K_FACTOR = 20.0 
HOME_ADVANTAGE = 48.0 
SEASON_CARRYOVER = 2 / 3

def expected_home_win_prob(home_elo: float, away_elo: float, home_advantage: float = HOME_ADVANTAGE) -> float:

    diff = home_elo + home_advantage - away_elo
    return 1.0 / (1.0 + 10 **(-diff / 400.0) )


def margin_multiplier(margin: float, winner_elo_diff: float) -> float:

    if margin == 0:
        return 1.0
    return math.log(abs(margin) + 1) * (2.2 / (winner_elo_diff * 0.001 + 2.2))


def update_ratings(

    home_elo: float, 
    away_elo: float, 
    home_score: float,
    away_score: float,
    k: float = K_FACTOR,
    home_advantage: float = HOME_ADVANTAGE,
) -> tuple[float, float]:

    expected = expected_home_win_prob(home_elo, away_elo, home_advantage)

    if home_score > away_score:
        actual = 1.0
        winner_diff = (home_elo + home_advantage) - away_elo
    elif home_score < away_score:
        actual = 0.0
        winner_diff = away_elo - (home_elo + home_advantage)
    else:
        actual = 0.5
        winner_diff = 0.0

    mult = margin_multiplier(home_score - away_score, winner_diff)
    delta = k * mult * (actual - expected)
    return home_elo + delta, away_elo - delta


def compute_elo(games: pd.DataFrame) -> tuple[pd.DataFrame, dict]:

    games = games.sort_values(["kickoff", "game_id"]).reset_index(drop=True)

    ratings: dict[str, float] = {}
    current_season = None
    rows = []

    for g in games.itertuples(index=False):

        if current_season is not None and g.season != current_season:
            for team in ratings:
                ratings[team] = START_RATING + (ratings[team] - START_RATING) * SEASON_CARRYOVER
        current_season = g.season

        home_elo = ratings.get(g.home_team, START_RATING)
        away_elo = ratings.get(g.away_team, START_RATING)

        rows.append(
            (home_elo, away_elo, home_elo - away_elo,
             expected_home_win_prob(home_elo, away_elo))
        )

        if pd.notna(g.home_team_score) and pd.notna(g.away_team_score):
            ratings[g.home_team], ratings[g.away_team] = update_ratings(
                home_elo, away_elo, g.home_team_score, g.away_team_score
            )

    feats = pd.DataFrame(rows, columns=["home_elo", "away_elo", "elo_diff", "elo_prob"])
    out = pd.concat([games.reset_index(drop=True), feats], axis=1)

    played = out["home_team_score"].notna() & out["away_team_score"].notna()
    home_win = pd.Series(float("nan"), index=out.index)
    home_win[played & (out["home_team_score"] > out["away_team_score"])] = 1.0
    home_win[played & (out["home_team_score"] < out["away_team_score"])] = 0.0
    out["home_win"] = home_win

    return out, ratings

def main() -> None:
    from sqlalchemy import text

    from src.db import engine

    games = pd.read_sql(
        text(
            "SELECT game_id, season, week, home_team, away_team, "
            "home_team_score, away_team_score, kickoff FROM games"
        ),
        engine,
    )
    feats, rating = compute_elo(games)

    first_season = int(feats["season"].min())

    test = feats[(feats["season"] > first_season) & feats["home_win"].notna()]

    p = test["elo_prob"].clip(1e-6, 1 - 1e-6)
    y = test["home_win"]
    accuracy = ((p > 0.5) == (y == 1.0)).mean()
    log_loss = -(y * p.map(math.log) + (1 - y) * (1 - p).map(math.log)).mean()

    print(f"Games loaded: {len(feats)}  (seasons {first_season}-{int(feats['season'].max())})")
    print(f"Evaluated on {len(test)} played games after the first season")
    print(f"Home team wins {y.mean():.3f} of games (the 'always pick home' baseline)")
    print(f"Elo accuracy: {accuracy:.3f}   log loss: {log_loss:.4f}   (coin flip = 0.6931)")
    if accuracy > 0.70:
        print("WARNING: accuracy this high usually means leakage. Check the code.")

    ranked = sorted(rating.items(), key=lambda kv: kv[1], reverse=True)
    print("Top 5:   ", ", ".join(f"{t} {r:.0f}" for t, r in ranked[:5]))
    print("Bottom 5:", ", ".join(f"{t} {r:.0f}" for t, r in ranked[-5:]))


if __name__ == "__main__":
    main()