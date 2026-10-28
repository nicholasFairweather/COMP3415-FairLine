Project Title: FairLine 

Team Members: Owen Moreau, Nicholas Fairweather, Daniel Kaci.

Project Description: A web-based sports betting predictor that uses historical and live game data to predict outcomes and aids the user with bets. 

## How to run

1. Start the Postgres container in Docker.
2. `cd backend` and `npm install`
3. Create `backend/.env` with DB_USER, DB_PASSWORD, JWT_SECRET, PORT
4. Load the tables and mock data:
   `docker exec -i CONTAINER psql -U fairline_dev -d fairline < src/db/schema.sql`
   `docker exec -i CONTAINER psql -U fairline_dev -d fairline < src/db/seed.sql`
5. `npm run dev` (runs on http://localhost:3001)

## How to test

`cd backend` then `npm test` (Postgres must be running)