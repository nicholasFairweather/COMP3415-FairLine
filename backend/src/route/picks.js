import express from "express";
import pool from "../db/pool.js";
import { requireLogin } from "../middleware/auth.js";

const router = express.Router();
router.use(requireLogin);

// Checks shared by create and edit. Returns { status, error } on failure or { game } on success.
async function checkPickable(gameId, team) {
    const result = await pool.query("SELECT * FROM games WHERE game_id = $1", [gameId]);
    const game = result.rows[0];

    if (!game) return { status: 404, error: "Game not found" };
    if (team !== game.home_team && team !== game.away_team) {
        return { status: 400, error: "Team must be one of the two teams in this game" };
    }
    if (new Date(game.kickoff) <= new Date()) return { status: 400, error: "Game already in progress" };
    return { game };
}

function isValidStake(stake) {
    return stake === undefined || stake === null || (typeof stake === "number" && stake > 0);
}

// POST /api/picks (US-05)  body: { game_id, team_picked, stake? }
router.post("/", async (req, res) => {
    const { game_id, team_picked, stake } = req.body;

    if (!Number.isInteger(game_id)) return res.status(400).json({ error: "game_id is required" });
    if (!isValidStake(stake)) return res.status(400).json({ error: "Stake must be greater than 0" });

    const check = await checkPickable(game_id, team_picked);
    if (check.error) return res.status(check.status).json({ error: check.error });

    try {
        const result = await pool.query(
            `INSERT INTO picks (user_id, game_id, team_picked, stake)
             VALUES ($1, $2, $3, $4) RETURNING *`,
            [req.user.userId, game_id, team_picked, stake ?? null]
        );
        res.status(201).json({ message: "Pick successfully saved", pick: result.rows[0] });
    } catch (err) {
        if (err.code === "23505") return res.status(409).json({ error: "Pick already selected" });
        throw err;
    }
});

// GET /api/picks (US-06) - the logged-in user's picks, newest game first
router.get("/", async (req, res) => {
    const result = await pool.query(
        `SELECT p.pick_id, p.game_id, p.team_picked, p.odds_at_pick, p.stake, p.status,
                p.created_at, p.updated_at,
                g.season, g.week, g.home_team, g.away_team, g.kickoff,
                g.home_team_score, g.away_team_score
         FROM picks p
         JOIN games g ON g.game_id = p.game_id
         WHERE p.user_id = $1
         ORDER BY g.kickoff DESC`,
        [req.user.userId]
    );
    res.json(result.rows);
});

// Finds a pick owned by the logged-in user, or null
async function findOwnPick(pickId, userId) {
    const result = await pool.query("SELECT * FROM picks WHERE pick_id = $1 AND user_id = $2", [pickId, userId]);
    return result.rows[0] || null;
}

// PUT /api/picks/:id (US-06 edit)  body: { team_picked?, stake? }
router.put("/:id", async (req, res) => {
    const pick = await findOwnPick(Number(req.params.id), req.user.userId);
    if (!pick) return res.status(404).json({ error: "Pick not found" });

    const team = req.body.team_picked ?? pick.team_picked;
    const stake = req.body.stake === undefined ? pick.stake : req.body.stake;
    if (!isValidStake(req.body.stake)) return res.status(400).json({ error: "Stake must be greater than 0" });

    const check = await checkPickable(pick.game_id, team);
    if (check.error) return res.status(check.status).json({ error: check.error });

    const result = await pool.query(
        `UPDATE picks SET team_picked = $1, stake = $2, updated_at = NOW()
         WHERE pick_id = $3 RETURNING *`,
        [team, stake, pick.pick_id]
    );
    res.json({ message: "Pick updated", pick: result.rows[0] });
});

// DELETE /api/picks/:id (US-06 delete). The confirm pop-up is handled by the frontend.
router.delete("/:id", async (req, res) => {
    const result = await pool.query(
        "DELETE FROM picks WHERE pick_id = $1 AND user_id = $2 RETURNING pick_id",
        [Number(req.params.id), req.user.userId]
    );
    if (result.rowCount === 0) return res.status(404).json({ error: "Pick not found" });
    res.json({ message: "Pick deleted" });
});

export default router;