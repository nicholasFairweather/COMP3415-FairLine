import express from "express";
import cors from "cors";
import router from "./route/route.js";
import authRouter from "./route/auth.js";

const app = express();

app.use(cors({ origin: 'http://localhost:5173' }));
app.use(express.json());
app.use(express.static("public"));
app.use("/api/games", router);
app.use("/api/auth", authRouter);

export default app;