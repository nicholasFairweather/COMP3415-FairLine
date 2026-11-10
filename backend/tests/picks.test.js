// These tests use the real database, so Docker Postgres must be running.
import request from "supertest";
import app from "../src/app.js";
import pool from "../src/db/pool.js";

// Signs up a user and returns a valid token for them
async function createUser(email) {
    await pool.query("DELETE FROM users WHERE email = $1", [email]);
    await request(app).post("/api/auth/signup").send({ email, password: "password123" });
    const res = await request(app).post("/api/auth/login").send({ email, password: "password123" });
    return res.body.token;
}

// Inserts a test game `daysFromNow` days away (negative = already started)
async function createGame(homeTeam, awayTeam, daysFromNow) {
    const result = await pool.query(
        `INSERT INTO games (season, week, home_team, away_team, kickoff)
         VALUES (2099, 1, $1, $2, NOW() + make_interval(days => $3)) RETURNING *`,
        [homeTeam, awayTeam, daysFromNow]
    );
    return result.rows[0];
}

async function deleteTestGames() {
    await pool.query("DELETE FROM games WHERE season = 2099");
}

const BETTOR = "picks-bettor@lakeheadu.ca";
const OTHER = "picks-other@lakeheadu.ca";

let token, otherToken, futureGame, futureGame2, startedGame;

beforeAll(async () => {
    await deleteTestGames();
    token = await createUser(BETTOR);
    otherToken = await createUser(OTHER);

    futureGame = await createGame("Test Home A", "Test Away A", 7);
    futureGame2 = await createGame("Test Home B", "Test Away B", 7);
    startedGame = await createGame("Test Home C", "Test Away C", -1);
});

afterAll(async () => {
    await deleteTestGames();
    await pool.query("DELETE FROM users WHERE email = ANY($1)", [[BETTOR, OTHER]]);
    await pool.end();
});

const auth = (t) => ({ Authorization: `Bearer ${t}` });

describe("US-05 Save a pick", () => {
    test("logged-in bettor saves a pick and gets 'Pick successfully saved'", async () => {
        const res = await request(app).post("/api/picks").set(auth(token))
            .send({ game_id: futureGame.game_id, team_picked: "Test Away A", stake: 25 });
        expect(res.status).toBe(201);
        expect(res.body.message).toBe("Pick successfully saved");
        expect(res.body.pick.team_picked).toBe("Test Away A");
        expect(res.body.pick.status).toBe("pending");
    });

    test("not logged in: no pick is saved and 401 is returned", async () => {
        const res = await request(app).post("/api/picks")
            .send({ game_id: futureGame2.game_id, team_picked: "Test Home B" });
        expect(res.status).toBe(401);
        const count = await pool.query("SELECT COUNT(*) FROM picks WHERE game_id = $1", [futureGame2.game_id]);
        expect(Number(count.rows[0].count)).toBe(0);
    });

    test("saving the same game twice gives 'Pick already selected'", async () => {
        const res = await request(app).post("/api/picks").set(auth(token))
            .send({ game_id: futureGame.game_id, team_picked: "Test Home A" });
        expect(res.status).toBe(409);
        expect(res.body.error).toBe("Pick already selected");
    });

    test("game already started gives 'Game already in progress'", async () => {
        const res = await request(app).post("/api/picks").set(auth(token))
            .send({ game_id: startedGame.game_id, team_picked: "Test Home C" });
        expect(res.status).toBe(400);
        expect(res.body.error).toBe("Game already in progress");
    });

    test("picking a team that is not in the game is rejected", async () => {
        const res = await request(app).post("/api/picks").set(auth(token))
            .send({ game_id: futureGame2.game_id, team_picked: "Toronto Argonauts" });
        expect(res.status).toBe(400);
    });

    test("unknown game gives 'Game not found'", async () => {
        const res = await request(app).post("/api/picks").set(auth(token))
            .send({ game_id: 999999, team_picked: "Test Home A" });
        expect(res.status).toBe(404);
        expect(res.body.error).toBe("Game not found");
    });
});

describe("US-06 View, edit and delete saved picks", () => {
    test("a user with no picks gets an empty list", async () => {
        const res = await request(app).get("/api/picks").set(auth(otherToken));
        expect(res.status).toBe(200);
        expect(res.body).toEqual([]);
    });

    test("a user sees only their own picks, with game details", async () => {
        const res = await request(app).get("/api/picks").set(auth(token));
        expect(res.status).toBe(200);
        expect(res.body).toHaveLength(1);
        expect(res.body[0]).toHaveProperty("home_team");
        expect(res.body[0]).toHaveProperty("odds_at_pick");
        expect(res.body[0]).toHaveProperty("status");
    });

    test("not logged in: viewing picks returns 401", async () => {
        const res = await request(app).get("/api/picks");
        expect(res.status).toBe(401);
    });

    test("editing a pick switches the team", async () => {
        const list = await request(app).get("/api/picks").set(auth(token));
        const pick = list.body.find((p) => p.game_id === futureGame.game_id);

        const res = await request(app).put(`/api/picks/${pick.pick_id}`).set(auth(token))
            .send({ team_picked: "Test Home A" });
        expect(res.status).toBe(200);
        expect(res.body.pick.team_picked).toBe("Test Home A");
    });

    test("another user cannot edit or delete my pick", async () => {
        const list = await request(app).get("/api/picks").set(auth(token));
        const pickId = list.body[0].pick_id;

        const edit = await request(app).put(`/api/picks/${pickId}`).set(auth(otherToken)).send({ stake: 5 });
        expect(edit.status).toBe(404);
        const del = await request(app).delete(`/api/picks/${pickId}`).set(auth(otherToken));
        expect(del.status).toBe(404);
    });

    test("deleting a pick removes it from the list", async () => {
        const list = await request(app).get("/api/picks").set(auth(token));
        const pickId = list.body[0].pick_id;

        const res = await request(app).delete(`/api/picks/${pickId}`).set(auth(token));
        expect(res.status).toBe(200);

        const after = await request(app).get("/api/picks").set(auth(token));
        expect(after.body.find((p) => p.pick_id === pickId)).toBeUndefined();
    });
});
