-- Mock games
INSERT INTO games (season, week, home_team, away_team, home_team_score, away_team_score, kickoff) VALUES
(2026, 8, 'Kansas City Chiefs',  'Las Vegas Raiders',    27, 17, '2026-10-25 16:25:00-04'),
(2026, 8, 'Buffalo Bills',       'Miami Dolphins',       24, 21, '2026-10-25 13:00:00-04'),
(2026, 9, 'Detroit Lions',       'Green Bay Packers',    NULL, NULL, '2026-11-01 13:00:00-05'),
(2026, 9, 'San Francisco 49ers', 'Seattle Seahawks',     NULL, NULL, '2026-11-01 16:05:00-05'),
(2026, 9, 'Baltimore Ravens',    'Cincinnati Bengals',   NULL, NULL, '2026-11-01 20:20:00-05')
ON CONFLICT DO NOTHING;