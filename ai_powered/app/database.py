import sqlite3
import os
from datetime import datetime

import config


DB_NAME = os.path.join(config.APP_DIR, "support_tickets.db")

TICKET_COLUMNS = {
    "confidence_score": "REAL DEFAULT 0.0",
    "resolution_status": "TEXT DEFAULT 'unresolved'",
    "retrieval_score": "REAL DEFAULT 0.0",
    "top_retrieval_score": "REAL DEFAULT 0.0",
    "kb_context_found": "INTEGER DEFAULT 0",
    "gap_group_key": "TEXT",
    "normalized_query": "TEXT",
    "suggested_kb_filename": "TEXT",
    "feedback_value": "TEXT",
    "feedback_at": "TIMESTAMP",
}

def get_db_connection():
    """Establishes and returns a connection to the SQLite database."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def _get_existing_columns(cursor, table_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}

def _ensure_ticket_columns(cursor):
    existing_columns = _get_existing_columns(cursor, "tickets")
    for column_name, column_definition in TICKET_COLUMNS.items():
        if column_name not in existing_columns:
            cursor.execute(
                f"ALTER TABLE tickets ADD COLUMN {column_name} {column_definition}"
            )

def init_db():
    """Initializes the database with the tickets table if it doesn't exist."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT NOT NULL,
                category TEXT,
                priority TEXT,
                user_id TEXT,
                ai_resolution TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(username)
            );
        ''')
        _ensure_ticket_columns(cursor)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL
            );
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_gap_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                gap_group_key TEXT NOT NULL UNIQUE,
                normalized_query TEXT NOT NULL,
                display_query TEXT NOT NULL,
                suggested_kb_filename TEXT,
                category TEXT,
                occurrence_count INTEGER DEFAULT 0,
                latest_ticket_id INTEGER,
                latest_confidence_score REAL DEFAULT 0.0,
                avg_confidence_score REAL DEFAULT 0.0,
                first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_alert_count INTEGER DEFAULT 0,
                last_alert_status TEXT,
                last_alert_message TEXT,
                last_alert_at TIMESTAMP,
                FOREIGN KEY(latest_ticket_id) REFERENCES tickets(id)
            );
        ''')
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tickets_user_created ON tickets(user_id, created_at DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(resolution_status, created_at DESC)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tickets_gap_key ON tickets(gap_group_key)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_gap_events_last_seen ON knowledge_gap_events(last_seen_at DESC)"
        )
        conn.commit()
    finally:
        conn.close()

def create_user(username, password_hash, role="user"):
    """Creates a new user in the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)", 
                       (username, password_hash, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # User already exists
    finally:
        conn.close()

def get_user(username):
    """Retrieves a user by username."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def update_user_password(username, new_password_hash):
    """Updates a user's password."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_password_hash, username))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def update_username(old_username, new_username):
    """Updates a user's username across all referenced tables."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username FROM users WHERE username = ?", (new_username,))
        if cursor.fetchone():
            return False
            
        cursor.execute("UPDATE users SET username = ? WHERE username = ?", (new_username, old_username))
        cursor.execute("UPDATE tickets SET user_id = ? WHERE user_id = ?", (new_username, old_username))
        conn.commit()
        return True
    except sqlite3.Error:
        conn.rollback()
        return False
    finally:
        conn.close()

def delete_user(username):
    """Deletes a user and their tickets from the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        # Delete user's tickets first
        cursor.execute("DELETE FROM tickets WHERE user_id = ?", (username,))
        # Delete user
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def delete_ticket(ticket_id):
    """Deletes a ticket by ID."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tickets WHERE id = ?", (ticket_id,))
        # Also clean up related knowledge gap events if needed, but not strictly necessary
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def get_all_users():
    """Retrieves all users."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT username, role FROM users")
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    print(f"Database {DB_NAME} initialized successfully.")
