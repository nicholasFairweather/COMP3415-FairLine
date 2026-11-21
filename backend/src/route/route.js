import express from "express";
import pool from "../db/pool.js";
import { marketSummary } from "../utils/oddsMath.js";
const router = express.Router();

// Each game with its latest odds and the newest real model prediction.
const GAMES_SQL = `
    SELECT g.*,
           o.bookmaker, o.home_odds, o.away_odds, o.fetched_at AS odds_fetched_at,
           p.home_win_prob::float AS home_win_prob, p.model_version
    FROM games g
    LEFT JOIN LATERAL (
        SELECT bookmaker, home_odds, away_odds, fetched_at
        FROM odds
        WHERE odds.game_id = g.game_id
        ORDER BY fetched_at DESC, bookmaker
        LIMIT 1
    ) o ON true
    LEFT JOIN LATERAL (
        SELECT home_win_prob, model_version
        FROM predictions
        WHERE predictions.game_id = g.game_id AND model_version <> 'seed'
        ORDER BY created_at DESC
        LIMIT 1
    ) p ON true`;

// GET /api/games (US-03) - every game, oldest kickoff first
router.get("/", async (req, res) => {
    const result = await pool.query(`${GAMES_SQL} ORDER BY g.kickoff`);
    res.json(result.rows);
});

// GET /api/games/:id (US-04) - one game plus implied/no-vig probability, model probability, edge and EV
router.get("/:id", async (req, res) => {
    const id = Number(req.params.id);
    if (!Number.isInteger(id)) return res.status(404).json({ error: "Game not found" });

    const result = await pool.query(`${GAMES_SQL} WHERE g.game_id = $1`, [id]);
    const game = result.rows[0];
    if (!game) return res.status(404).json({ error: "Game not found" });

    res.json({ ...game, market: marketSummary(game.home_odds, game.away_odds, game.home_win_prob) });
});

export default router;