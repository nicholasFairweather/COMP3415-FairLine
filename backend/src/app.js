import express from "express";
import cors from "cors";
import router from "./route/route.js";
import authRouter from "./route/auth.js";
import picksRouter from "./route/picks.js";

const app = express();

app.use(cors({ origin: 'http://localhost:5173' }));
app.use(express.json());
app.use(express.static("../frontend/public"));
app.use("/api/games", router);
app.use("/api/auth", authRouter);
app.use("/api/picks", picksRouter);

// Any error thrown in a route ends up here (Express 5 forwards async errors automatically)
app.use((err, req, res, next) => {
    console.error(err);
    res.status(500).json({ error: "Internal Server Error" });
});

export default app;