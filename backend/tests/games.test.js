// These tests use the real database, so Docker Postgres must be running.
import request from "supertest";
import app from "../src/app.js";
import pool from "../src/db/pool.js";

let withOdds, withoutOdds, oddsNoModel;

beforeAll(async () => {
    await pool.query("DELETE FROM games WHERE season = 2098");
    const games = await pool.query(
        `INSERT INTO games (season, week, home_team, away_team, kickoff) VALUES
         (2098, 1, 'Odds Home', 'Odds Away', NOW() + INTERVAL '3 days'),
         (2098, 1, 'NoOdds Home', 'NoOdds Away', NOW() + INTERVAL '3 days'),
         (2098, 1, 'OddsOnly Home', 'OddsOnly Away', NOW() + INTERVAL '3 days')
         RETURNING *`
    );
    [withOdds, withoutOdds, oddsNoModel] = games.rows;

    await pool.query(
        `INSERT INTO odds (game_id, bookmaker, home_odds, away_odds, fetched_at) VALUES
         ($1, 'oldbook', -110, -110, NOW() - INTERVAL '2 hours'),
         ($1, 'draftkings', -150, 130, NOW()),
         ($2, 'draftkings', -150, 130, NOW())`,
        [withOdds.game_id, oddsNoModel.game_id]
    );

    // A real model prediction for the first game, plus "seed" placeholders that must be ignored
    await pool.query(
        `INSERT INTO predictions (game_id, home_win_prob, model_version) VALUES
         ($1, 0.62, 'elo_logreg_v1'),
         ($1, 0.30, 'seed'),
         ($2, 0.45, 'seed')`,
        [withOdds.game_id, oddsNoModel.game_id]
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

    test("includes the real model's win probability, not the seed placeholder", async () => {
        const res = await request(app).get("/api/games");
        const game = res.body.find((g) => g.game_id === withOdds.game_id);
        expect(game).toMatchObject({ home_win_prob: 0.62, model_version: "elo_logreg_v1" });
    });

    test("a game with no odds has null odds fields", async () => {
        const res = await request(app).get("/api/games");
        const game = res.body.find((g) => g.game_id === withoutOdds.game_id);
        expect(game).toMatchObject({ bookmaker: null, home_odds: null, away_odds: null, home_win_prob: null });
    });

    test("each game appears only once even with several odds snapshots", async () => {
        const res = await request(app).get("/api/games");
        const copies = res.body.filter((g) => g.game_id === withOdds.game_id);
        expect(copies).toHaveLength(1);
    });
});

describe("GET /api/games/:id (US-04)", () => {
    test("returns the game with implied, no-vig, model probability, edge and EV", async () => {
        const res = await request(app).get(`/api/games/${withOdds.game_id}`);
        expect(res.status).toBe(200);
        expect(res.body).toMatchObject({ home_team: "Odds Home", home_odds: -150, away_odds: 130 });
        expect(res.body.market.home).toEqual({
            implied_prob: 0.6, no_vig_prob: 0.5798, model_prob: 0.62, edge: 0.0402, ev: 0.0333,
        });
        expect(res.body.market.away.model_prob).toBe(0.38);
    });

    test("without a model prediction, odds math is shown but model fields are null (seed rows don't count)", async () => {
        const res = await request(app).get(`/api/games/${oddsNoModel.game_id}`);
        expect(res.status).toBe(200);
        expect(res.body.home_win_prob).toBeNull();
        expect(res.body.market.home).toEqual({
            implied_prob: 0.6, no_vig_prob: 0.5798, model_prob: null, edge: null, ev: null,
        });
    });

    test("market is null when there are no odds", async () => {
        const res = await request(app).get(`/api/games/${withoutOdds.game_id}`);
        expect(res.status).toBe(200);
        expect(res.body.market).toBeNull();
    });

    test("unknown game gives 404 'Game not found'", async () => {
        const res = await request(app).get("/api/games/999999");
        expect(res.status).toBe(404);
        expect(res.body.error).toBe("Game not found");
    });

    test("a non-number id gives 404", async () => {
        const res = await request(app).get("/api/games/abc");
        expect(res.status).toBe(404);
    });
});