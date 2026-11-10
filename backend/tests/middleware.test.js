// Unit tests for the auth middleware (no database needed)
import { jest } from "@jest/globals";
import jwt from "jsonwebtoken";
import { requireLogin, signToken } from "../src/middleware/auth.js";

function mockRes() {
    const res = {};
    res.status = jest.fn(() => res);
    res.json = jest.fn(() => res);
    return res;
}

describe("requireLogin", () => {
    test("rejects a request with no Authorization header", () => {
        const res = mockRes();
        const next = jest.fn();
        requireLogin({ headers: {} }, res, next);
        expect(res.status).toHaveBeenCalledWith(401);
        expect(next).not.toHaveBeenCalled();
    });

    test("rejects a token signed with the wrong secret", () => {
        const token = jwt.sign({ userId: 1, role: "bettor" }, "not-the-real-secret");
        const res = mockRes();
        const next = jest.fn();
        requireLogin({ headers: { authorization: `Bearer ${token}` } }, res, next);
        expect(res.status).toHaveBeenCalledWith(401);
        expect(next).not.toHaveBeenCalled();
    });

    test("rejects an expired token", () => {
        const token = jwt.sign({ userId: 1, role: "bettor" }, process.env.JWT_SECRET, { expiresIn: -10 });
        const res = mockRes();
        const next = jest.fn();
        requireLogin({ headers: { authorization: `Bearer ${token}` } }, res, next);
        expect(res.status).toHaveBeenCalledWith(401);
    });

    test("accepts a valid token and sets req.user", () => {
        const token = signToken({ user_id: 7, role: "bettor" });
        const req = { headers: { authorization: `Bearer ${token}` } };
        const next = jest.fn();
        requireLogin(req, mockRes(), next);
        expect(next).toHaveBeenCalled();
        expect(req.user).toEqual({ userId: 7, role: "bettor" });
    });
});