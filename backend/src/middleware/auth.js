import jwt from "jsonwebtoken";

export function signToken(user) {
    return jwt.sign(
        { userId: user.user_id, role: user.role },
        process.env.JWT_SECRET,
        { expiresIn: "2h" }
    );
}

// Rejects the request with 401 unless it has a valid "Authorization: Bearer <token>" header.
// On success, req.user = { userId, role }.
export function requireLogin(req, res, next) {
    const header = req.headers.authorization || "";
    const [scheme, token] = header.split(" ");

    if (scheme !== "Bearer" || !token) {
        return res.status(401).json({ error: "You must be logged in" });
    }

    try {
        const payload = jwt.verify(token, process.env.JWT_SECRET);
        req.user = { userId: payload.userId, role: payload.role };
        next();
    } catch {
        res.status(401).json({ error: "You must be logged in" });
    }
}