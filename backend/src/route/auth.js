import express from "express";
import bcrypt from "bcryptjs";
import pool from "../db/pool.js";
import { isValidEmail, isValidPassword } from "../utils/validation.js";
import { signToken, requireLogin } from "../middleware/auth.js";

const router = express.Router();

function normalizeEmail(email) {
    return typeof email === "string" ? email.trim().toLowerCase() : email;
}

// POST /api/auth/signup (US-01)
router.post("/signup", async (req, res) => {
    const email = normalizeEmail(req.body.email);
    const { password } = req.body;

    if (!isValidEmail(email)) return res.status(400).json({ error: "Invalid email address" });
    if (!isValidPassword(password)) return res.status(400).json({ error: "Password must be more than 8 characters" });

    const hash = await bcrypt.hash(password, 10);

    try {
        const result = await pool.query(
            "INSERT INTO users (email, password_hash) VALUES ($1, $2) RETURNING user_id, email, role",
            [email, hash]
        );
        const user = result.rows[0];
        res.status(201).json({ token: signToken(user), user });
    } catch (err) {
        // 23505 = unique violation on email
        if (err.code === "23505") return res.status(409).json({ error: "Email already in use" });
        throw err;
    }
});

// POST /api/auth/login (US-02)
router.post("/login", async (req, res) => {
    const email = normalizeEmail(req.body.email);
    const { password } = req.body;

    if (!isValidEmail(email)) return res.status(400).json({ error: "Invalid email address" });

    const result = await pool.query("SELECT * FROM users WHERE email = $1", [email]);
    const user = result.rows[0];

    const passwordOk = user && typeof password === "string" && (await bcrypt.compare(password, user.password_hash));
    if (!passwordOk) {
        return res.status(401).json({ error: "Invalid email or password" });
    }

    res.json({
        token: signToken(user),
        user: { user_id: user.user_id, email: user.email, role: user.role },
    });
});

// GET /api/auth/me - who is logged in
router.get("/me", requireLogin, (req, res) => {
    res.json(req.user);
});

export default router;
