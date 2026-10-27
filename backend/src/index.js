import "dotenv/config";
import express from "express";
import cors from "cors";
const port = process.env.PORT || 3001;
import router from "./route/route.js";

const app = express();

app.use(cors({ origin: 'http://localhost:5173' }));
app.use(express.json());
app.use("/api/games", router);


app.listen(port, () => { console.log(`Server is running on port ${port}`); });
