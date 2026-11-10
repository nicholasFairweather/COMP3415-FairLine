import os 
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

# Define the path to the .env file in the ml directory
ML_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ML_DIR / ".env")

Database_URL = os.getenv("DATABASE_URL")
if not Database_URL:
    raise RuntimeError("DATABASE_URL environment variable is not set.")

#pool_pre_ping drops dead connections from the pool and reconnects to the database
engine = create_engine(Database_URL, pool_pre_ping=True)

# Check the connection to the database
def check_connection() -> None:
    """Print whether the connection to the database is successful or not."""
    # Check if the engine is created successfully
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("Database connection successful.")
    except Exception as e:
        print(f"Database connection failed: {e}")

    tables = inspect(engine).get_table_names()
    print("Tables:", ",".join(sorted(tables)) if tables else "No tables found.")

    # Check the number of rows in the "games" table if it exists
    if "games" in tables:
        with engine.connect() as conn:
            count = conn.execute(text("SELECT COUNT(*) FROM games")).scalar()
            print(f"games rows: {count}")

if __name__ == "__main__":
    check_connection()