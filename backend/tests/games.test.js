// These tests use the real database, so Docker Postgres must be running.
import request from "supertest";
import app from "../src/app.js";
import pool from "../src/db/pool.js";

let withOdds, withoutOdds;

beforeAll(async () => {
    await pool.query("DELETE FROM games WHERE season = 2098");
    const games = await pool.query(
        `INSERT INTO games (season, week, home_team, away_team, kickoff) VALUES
         (2098, 1, 'Odds Home', 'Odds Away', NOW() + INTERVAL '3 days'),
         (2098, 1, 'NoOdds Home', 'NoOdds Away', NOW() + INTERVAL '3 days')
         RETURNING *`
    );
    [withOdds, withoutOdds] = games.rows;

    await pool.query(
        `INSERT INTO odds (game_id, bookmaker, home_odds, away_odds, fetched_at) VALUES
         ($1, 'oldbook', -110, -110, NOW() - INTERVAL '2 hours'),
         ($1, 'draftkings', -150, 130, NOW())`,
        [withOdds.game_id]
    );
});

afterAll(async () => {
    await pool.query("DELETE FROM games WHERE season = 2098");
    await pool.end();
});

describe("GET /api/games (US-03)", () => {
    test("returns games with their latest odds", async () => {
        const res = await request(app).get("/api/games");
        expect(res.status).toBe(200);

        const game = res.body.find((g) => g.game_id === withOdds.game_id);
        expect(game).toMatchObject({ bookmaker: "draftkings", home_odds: -150, away_odds: 130 });
        expect(game.odds_fetched_at).toBeDefined();
    });

    test("a game with no odds has null odds fields", async () => {
        const res = await request(app).get("/api/games");
        const game = res.body.find((g) => g.game_id === withoutOdds.game_id);
        expect(game).toMatchObject({ bookmaker: null, home_odds: null, away_odds: null });
    });

    test("each game appears only once even with several odds snapshots", async () => {
        const res = await request(app).get("/api/games");
        const copies = res.body.filter((g) => g.game_id === withOdds.game_id);
        expect(copies).toHaveLength(1);
    });
});