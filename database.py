import sqlite3
import bcrypt
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "mindcare.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            user_message TEXT NOT NULL,
            bot_reply TEXT NOT NULL,
            stress_score INTEGER DEFAULT 0,
            anxiety_score INTEGER DEFAULT 0,
            mood_label TEXT DEFAULT 'neutral',
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.commit()
    conn.close()


def create_user(username: str, password: str) -> dict:
    """Register a new user. Returns {'success': bool, 'message': str}."""
    conn = get_connection()
    try:
        hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
        conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hashed.decode("utf-8")),
        )
        conn.commit()
        return {"success": True, "message": "Account created successfully!"}
    except sqlite3.IntegrityError:
        return {"success": False, "message": "Username already exists."}
    finally:
        conn.close()


def verify_user(username: str, password: str) -> dict:
    """Verify login credentials. Returns {'success': bool, 'user_id': int|None}."""
    conn = get_connection()
    row = conn.execute(
        "SELECT id, password_hash FROM users WHERE username = ?", (username,)
    ).fetchone()
    conn.close()

    if row is None:
        return {"success": False, "user_id": None, "message": "User not found."}

    if bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
        return {"success": True, "user_id": row["id"], "message": "Login successful!"}
    else:
        return {"success": False, "user_id": None, "message": "Incorrect password."}


def save_session(user_id: int, user_message: str, bot_reply: str,
                 stress_score: int = 0, anxiety_score: int = 0,
                 mood_label: str = "neutral"):
    """Save a chat session with mood scores."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO sessions
           (user_id, user_message, bot_reply, stress_score, anxiety_score, mood_label)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, user_message, bot_reply, stress_score, anxiety_score, mood_label),
    )
    conn.commit()
    conn.close()


def get_user_sessions(user_id: int) -> list:
    """Get all sessions for a user, ordered by time."""
    conn = get_connection()
    rows = conn.execute(
        """SELECT timestamp, user_message, bot_reply,
                  stress_score, anxiety_score, mood_label
           FROM sessions WHERE user_id = ?
           ORDER BY timestamp ASC""",
        (user_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# Initialize database on import
init_db()
