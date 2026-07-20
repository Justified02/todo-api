import os
import psycopg
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    return psycopg.connect(os.environ["DATABASE_URL"])

def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)
    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count == 0:
        conn.execute(
            "INSERT INTO tasks (title, done) VALUES (%s, %s), (%s, %s), (%s, %s)",
            ("Buy milk", False, "Walk the dog", False, "Write code", True)
        )
    conn.commit()
    conn.close()