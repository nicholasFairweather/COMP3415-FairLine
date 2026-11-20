import express from "express";
import pool from "../db/pool.js";
const router = express.Router();

router.get("/", async (req, res) => {
    const result = await pool.query(
        `SELECT g.*, o.bookmaker, o.home_odds, o.away_odds, o.fetched_at AS odds_fetched_at
         FROM games g
         LEFT JOIN LATERAL (
             SELECT bookmaker, home_odds, away_odds, fetched_at
             FROM odds
             WHERE odds.game_id = g.game_id
             ORDER BY fetched_at DESC, bookmaker
             LIMIT 1
         ) o ON true
         ORDER BY g.kickoff`
    );
    res.json(result.rows);
});

export default router;