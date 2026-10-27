CREATE TABLE games(
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