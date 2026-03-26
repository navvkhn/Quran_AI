import sqlite3
from datetime import datetime
from typing import Optional

USER_DB = "dev_bot_v2.db"
QURAN_DB = "quran.db"

def get_db_connection(db_name):
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    return conn

def init_user_db():
    with get_db_connection(USER_DB) as db:
        db.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY, 
                username TEXT UNIQUE, 
                hashed_password TEXT, 
                email TEXT, 
                disabled BOOLEAN
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS threads (
                id INTEGER PRIMARY KEY, 
                user_id INTEGER, 
                created_at TIMESTAMP
            )
        ''')
        db.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY, 
                thread_id INTEGER, 
                role TEXT, 
                content TEXT, 
                timestamp TIMESTAMP
            )
        ''')
        db.commit()

# --- User & Chat Functions ---

def get_user(username: str):
    with get_db_connection(USER_DB) as db:
        return db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

def create_user(username: str, hashed_password: str, email: str = None):
    with get_db_connection(USER_DB) as db:
        db.execute(
            'INSERT INTO users (username, hashed_password, email, disabled) VALUES (?, ?, ?, ?)', 
            (username, hashed_password, email, False)
        )
        db.commit()

def save_msg(thread_id: int, role: str, content: str):
    with get_db_connection(USER_DB) as db:
        db.execute(
            'INSERT INTO messages (thread_id, role, content, timestamp) VALUES (?, ?, ?, ?)',
            (thread_id, role, content, datetime.utcnow())
        )
        db.commit()

def load_messages(thread_id: int):
    with get_db_connection(USER_DB) as db:
        cursor = db.execute(
            'SELECT role, content FROM messages WHERE thread_id = ? ORDER BY timestamp ASC',
            (thread_id,)
        )
        return [{"role": row["role"], "content": row["content"]} for row in cursor.fetchall()]

# --- RAG: Quran Search Function ---

def search_quran(query_text: str, edition_id: int = 77) -> list:
    """
    Searches the Quran database for keywords. 
    Edition 77 is assumed to be an English translation based on typical schemas.
    """
    try:
        with get_db_connection(QURAN_DB) as conn:
            search_query = f"%{query_text}%"
            # Adjust this SQL query to match your exact quran.db schema
            results = conn.execute('''
                SELECT s.name_en, a.ayah_id, a.text as arabic_text, ed.text as translation
                FROM quran_ayahs a
                JOIN quran_surahs s ON a.surah_id = s.id
                JOIN quran_ayat_edition ed ON a.surah_id = ed.surah_id AND a.ayah_id = ed.ayah_id
                WHERE ed.text LIKE ? AND ed.edition_id = ?
                LIMIT 4
            ''', (search_query, edition_id)).fetchall()
        return [dict(row) for row in results]
    except sqlite3.OperationalError as e:
        print(f"Quran DB Error: Ensure quran.db exists and schema matches. Details: {e}")
        return []
