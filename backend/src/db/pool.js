import pg from "pg";

const Pool = pg.Pool;

const pool = new Pool({
    user: process.env.DB_USER,
    host: "localhost",
    database: "fairline",
    password: process.env.DB_PASSWORD,
    port: 5432,
});


export default pool;