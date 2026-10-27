import express from "express";
import pool from "../db/pool.js";
const router = express.Router();

// Get all posts
router.get("/", async (req, res) => {
    try {
        const result = await pool.query("SELECT * FROM games");
        res.json(result.rows);
    } catch (err) {
        console.error(err);
        res.status(500).json({ error: "Internal Server Error" });
    }
});

export default router;