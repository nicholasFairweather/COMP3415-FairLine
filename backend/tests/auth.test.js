// these tests use the real database, so Docker Postgres must be running.
import request from "supertest";
import app from "../src/app.js";
import pool from "../src/db/pool.js";

const EMAIL = "test@lakeheadu.ca";

beforeAll(async () => {
    await pool.query("DELETE FROM users WHERE email = $1", [EMAIL]);
});

afterAll(async () => {
    await pool.query("DELETE FROM users WHERE email = $1", [EMAIL]);
    await pool.end();
});

describe("US-01 Create Account", () => {
    test("valid email and password creates an account", async () => {
        const res = await request(app).post("/api/auth/signup").send({ email: EMAIL, password: "password123" });
        expect(res.status).toBe(201);
        expect(res.body.token).toBeDefined();
    });

    test("email already in use is rejected", async () => {
        const res = await request(app).post("/api/auth/signup").send({ email: EMAIL, password: "password123" });
        expect(res.status).toBe(409);
        expect(res.body.error).toBe("Email already in use");
    });

    test("invalid email is rejected", async () => {
        const res = await request(app).post("/api/auth/signup").send({ email: "bad-email", password: "password123" });
        expect(res.status).toBe(400);
        expect(res.body.error).toBe("Invalid email address");
    });

    test("short password is rejected", async () => {
        const res = await request(app).post("/api/auth/signup").send({ email: "new@lakeheadu.ca", password: "short" });
        expect(res.status).toBe(400);
        expect(res.body.error).toBe("Password must be more than 8 characters");
    });

    test("password is stored hashed, not in plain text", async () => {
        const result = await pool.query("SELECT password_hash FROM users WHERE email = $1", [EMAIL]);
        expect(result.rows[0].password_hash).not.toBe("password123");
    });
});

describe("US-02 Login", () => {
    test("correct email and password logs in", async () => {
        const res = await request(app).post("/api/auth/login").send({ email: EMAIL, password: "password123" });
        expect(res.status).toBe(200);
        expect(res.body.token).toBeDefined();
    });

    test("wrong password shows 'Invalid email or password'", async () => {
        const res = await request(app).post("/api/auth/login").send({ email: EMAIL, password: "wrongpass" });
        expect(res.status).toBe(401);
        expect(res.body.error).toBe("Invalid email or password");
    });

    test("/me works with a token and fails without one", async () => {
        const login = await request(app).post("/api/auth/login").send({ email: EMAIL, password: "password123" });
        const withToken = await request(app).get("/api/auth/me").set("Authorization", `Bearer ${login.body.token}`);
        expect(withToken.status).toBe(200);

        const withoutToken = await request(app).get("/api/auth/me");
        expect(withoutToken.status).toBe(401);
    });
});