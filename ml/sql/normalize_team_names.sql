BEGIN;

-- Step 1: remove seed games that duplicate a real game (the rows listed are deleted)
WITH m(full_name, abbr) AS (VALUES
    ('Arizona Cardinals', 'ARI'),
    ('Atlanta Falcons', 'ATL'),
    ('Baltimore Ravens', 'BAL'),
    ('Buffalo Bills', 'BUF'),
    ('Carolina Panthers', 'CAR'),
    ('Chicago Bears', 'CHI'),
    ('Cincinnati Bengals', 'CIN'),
    ('Cleveland Browns', 'CLE'),
    ('Dallas Cowboys', 'DAL'),
    ('Denver Broncos', 'DEN'),
    ('Detroit Lions', 'DET'),
    ('Green Bay Packers', 'GB'),
    ('Houston Texans', 'HOU'),
    ('Indianapolis Colts', 'IND'),
    ('Jacksonville Jaguars', 'JAX'),
    ('Kansas City Chiefs', 'KC'),
    ('Las Vegas Raiders', 'LV'),
    ('Los Angeles Chargers', 'LAC'),
    ('Los Angeles Rams', 'LA'),
    ('Miami Dolphins', 'MIA'),
    ('Minnesota Vikings', 'MIN'),
    ('New England Patriots', 'NE'),
    ('New Orleans Saints', 'NO'),
    ('New York Giants', 'NYG'),
    ('New York Jets', 'NYJ'),
    ('Philadelphia Eagles', 'PHI'),
    ('Pittsburgh Steelers', 'PIT'),
    ('San Francisco 49ers', 'SF'),
    ('Seattle Seahawks', 'SEA'),
    ('Tampa Bay Buccaneers', 'TB'),
    ('Tennessee Titans', 'TEN'),
    ('Washington Commanders', 'WAS')
)
DELETE FROM games
WHERE game_id IN (
    SELECT s.game_id
    FROM games s
    JOIN m mh ON s.home_team = mh.full_name
    JOIN m ma ON s.away_team = ma.full_name
    JOIN games r ON r.home_team = mh.abbr
                AND r.away_team = ma.abbr
                AND r.season = s.season
                AND r.week = s.week
)
RETURNING game_id, season, week, home_team, away_team;

-- Step 2: convert the remaining full names to abbreviations
WITH m(full_name, abbr) AS (VALUES
    ('Arizona Cardinals', 'ARI'),
    ('Atlanta Falcons', 'ATL'),
    ('Baltimore Ravens', 'BAL'),
    ('Buffalo Bills', 'BUF'),
    ('Carolina Panthers', 'CAR'),
    ('Chicago Bears', 'CHI'),
    ('Cincinnati Bengals', 'CIN'),
    ('Cleveland Browns', 'CLE'),
    ('Dallas Cowboys', 'DAL'),
    ('Denver Broncos', 'DEN'),
    ('Detroit Lions', 'DET'),
    ('Green Bay Packers', 'GB'),
    ('Houston Texans', 'HOU'),
    ('Indianapolis Colts', 'IND'),
    ('Jacksonville Jaguars', 'JAX'),
    ('Kansas City Chiefs', 'KC'),
    ('Las Vegas Raiders', 'LV'),
    ('Los Angeles Chargers', 'LAC'),
    ('Los Angeles Rams', 'LA'),
    ('Miami Dolphins', 'MIA'),
    ('Minnesota Vikings', 'MIN'),
    ('New England Patriots', 'NE'),
    ('New Orleans Saints', 'NO'),
    ('New York Giants', 'NYG'),
    ('New York Jets', 'NYJ'),
    ('Philadelphia Eagles', 'PHI'),
    ('Pittsburgh Steelers', 'PIT'),
    ('San Francisco 49ers', 'SF'),
    ('Seattle Seahawks', 'SEA'),
    ('Tampa Bay Buccaneers', 'TB'),
    ('Tennessee Titans', 'TEN'),
    ('Washington Commanders', 'WAS')
)
UPDATE games AS g SET home_team = m.abbr FROM m WHERE g.home_team = m.full_name;

WITH m(full_name, abbr) AS (VALUES
    ('Arizona Cardinals', 'ARI'),
    ('Atlanta Falcons', 'ATL'),
    ('Baltimore Ravens', 'BAL'),
    ('Buffalo Bills', 'BUF'),
    ('Carolina Panthers', 'CAR'),
    ('Chicago Bears', 'CHI'),
    ('Cincinnati Bengals', 'CIN'),
    ('Cleveland Browns', 'CLE'),
    ('Dallas Cowboys', 'DAL'),
    ('Denver Broncos', 'DEN'),
    ('Detroit Lions', 'DET'),
    ('Green Bay Packers', 'GB'),
    ('Houston Texans', 'HOU'),
    ('Indianapolis Colts', 'IND'),
    ('Jacksonville Jaguars', 'JAX'),
    ('Kansas City Chiefs', 'KC'),
    ('Las Vegas Raiders', 'LV'),
    ('Los Angeles Chargers', 'LAC'),
    ('Los Angeles Rams', 'LA'),
    ('Miami Dolphins', 'MIA'),
    ('Minnesota Vikings', 'MIN'),
    ('New England Patriots', 'NE'),
    ('New Orleans Saints', 'NO'),
    ('New York Giants', 'NYG'),
    ('New York Jets', 'NYJ'),
    ('Philadelphia Eagles', 'PHI'),
    ('Pittsburgh Steelers', 'PIT'),
    ('San Francisco 49ers', 'SF'),
    ('Seattle Seahawks', 'SEA'),
    ('Tampa Bay Buccaneers', 'TB'),
    ('Tennessee Titans', 'TEN'),
    ('Washington Commanders', 'WAS')
)
UPDATE games AS g SET away_team = m.abbr FROM m WHERE g.away_team = m.full_name;

COMMIT;

-- Check: every team should now be an abbreviation (no spaces).
SELECT home_team, COUNT(*) FROM games GROUP BY home_team ORDER BY home_team;