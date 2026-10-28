import express from "express";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import pool from "../db/pool.js";
import { isValidEmail, isValidPassword } from "../utils/validation.js";

const router = express.Router();

// sign up
router.post("/signup", async (req, res) => {
    const { email, password } = req.body;

    if (!isValidEmail(email)) return res.status(400).json({ error: "Invalid email address" });
    if (!isValidPassword(password)) return res.status(400).json({ error: "Password must be more than 8 characters" });

    const existing = await pool.query("SELECT * FROM users WHERE email = $1", [email]);
    if (existing.rows.length > 0) return res.status(409).json({ error: "Email already in use" });

    const hash = await bcrypt.hash(password, 10);
    const result = await pool.query(
        "INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING *",
        [email, hash]
    );
    const user = result.rows[0];

    const token = jwt.sign({ userId: user.user_id, role: user.role }, process.env.JWT_SECRET);
    res.status(201).json({ token });
});

// login
router.post("/login", async (req, res) => {
    const { email, password } = req.body;

    const result = await pool.query("SELECT * FROM users WHERE email = $1", [email]);
    const user = result.rows[0];

    if (!user || !(await bcrypt.compare(password, user.password_hash))) {
        return res.status(401).json({ error: "Invalid email or password" });
    }

    const token = jwt.sign({ userId: user.user_id, role: user.role }, process.env.JWT_SECRET);
    res.json({ token });
});

// check who is logged in
router.get("/me", (req, res) => {
    try {
        const token = req.headers.authorization.split(" ")[1];
        res.json(jwt.verify(token, process.env.JWT_SECRET));
    } catch {
        res.status(401).json({ error: "You must be logged in" });
    }
});

export default router;