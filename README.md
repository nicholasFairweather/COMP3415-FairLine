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


## ML / Data Pipeline (`ml/`)

The `ml/` folder holds the Python code for data ingestion, the prediction model, and the betting math (no-vig probability, EV, Kelly). It writes to the same PostgreSQL database the backend reads from.

### Prerequisites
- Python 3.10 or newer
- Docker running with the project's PostgreSQL container (see the backend setup above)
- A free API key from [The Odds API](https://the-odds-api.com)

### First-time setup

From the repo root:

```bash
cd ml
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # Windows: copy .env.example .env
```

Then open `ml/.env` and fill in your values:

```
DATABASE_URL=postgresql+psycopg2://USER:PASSWORD@localhost:5432/fairline
ODDS_API_KEY=your_key_here
```

Use the same database credentials as `backend/.env`. Never commit `.env`.

### Every time you work on the ML code

1. Pull the latest changes: `git pull`
2. Activate the virtual environment: `source .venv/bin/activate`
3. If `requirements.txt` changed, run `pip install -r requirements.txt`

### Running the tests

```bash
cd ml
pytest
```

### Running the scripts

Run these from the `ml/` folder with the virtual environment active. (Update this list as scripts are added.)

```bash
python -m src.ingest.load_games     # load NFL games from nflverse into Postgres
python -m src.ingest.fetch_odds     # fetch current odds from The Odds API
python -m src.model.train_baseline  # train the baseline model
python -m src.model.predict         # write predictions to the database
```

### Adding a new Python package

```bash
pip install package-name
pip freeze > requirements.txt
```

Commit the updated `requirements.txt` so everyone gets the same versions.

### Notes
- The Odds API free tier has a limited monthly quota. Save responses to a JSON file while developing instead of calling the API repeatedly.
- Model features may only use information available before kickoff, to avoid data leakage.
- The folder layout is documented in the repo structure above. Keep pure logic (like `odds_math.py`) separate from database and API code so it stays easy to test.