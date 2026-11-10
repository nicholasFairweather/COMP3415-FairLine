CREATE TABLE IF NOT EXISTS games(
    game_id serial primary key, 
    season INTEGER NOT NULL, 
    week INTEGER NOT NULL, 
    home_team VARCHAR(100) NOT NULL, 
    away_team VARCHAR(100) NOT NULL, 
    home_team_score INTEGER, 
    away_team_score INTEGER, 
    kickoff TIMESTAMPTZ NOT NULL, 
    UNIQUE (week, home_team, away_team, season)
);

CREATE TABLE IF NOT EXISTS users(
    user_id serial primary key,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'bettor'
);

CREATE TABLE IF NOT EXISTS picks(
    pick_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    game_id INTEGER NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,
    team_picked VARCHAR(100) NOT NULL,
    odds_at_pick INTEGER,
    stake NUMERIC(10, 2) CHECK (stake IS NULL OR stake > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'won', 'lost')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (user_id, game_id)
);

CREATE TABLE IF NOT EXISTS odds(
    odds_id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,
    bookmaker VARCHAR(50) NOT NULL,
    home_odds INTEGER NOT NULL,          -- American odds, e.g. -110
    away_odds INTEGER NOT NULL,
    fetched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (game_id, bookmaker, fetched_at)
);

CREATE INDEX IF NOT EXISTS idx_odds_game_fetched ON odds (game_id, fetched_at DESC);

CREATE TABLE IF NOT EXISTS predictions(
    prediction_id SERIAL PRIMARY KEY,
    game_id INTEGER NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,
    home_win_prob NUMERIC(5, 4) NOT NULL CHECK (home_win_prob >= 0 AND home_win_prob <= 1),
    model_version VARCHAR(50) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (game_id, model_version)
);