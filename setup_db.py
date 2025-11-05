import psycopg2
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# 🔐 Replace with your Neon connection URL from the console
NEON_DB_URL = os.getenv("NEON_DB_URL")

# 📄 Read schema SQL from file (absolute path)
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "database_schema.sql")
with open(SCHEMA_PATH, "r") as file:
    schema_sql = file.read()

# 🚀 Connect and execute
try:
    with psycopg2.connect(NEON_DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(schema_sql)
            conn.commit()
            print("✅ Schema applied successfully (tables, seed data, and SQL functions)!")
except Exception as e:
    print("❌ Error creating tables:", e)
