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
