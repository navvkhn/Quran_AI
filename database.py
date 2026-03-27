import json
import sqlite3
import os

USER_DB = "dev_bot_v2.db"
QURAN_JSON = "quran.json"
CHAPTERS_DIR = "chapters"

def get_user_db():
    conn = sqlite3.connect(USER_DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_user_db():
    with get_user_db() as db:
        # 1. Create base table structure
        db.execute('''CREATE TABLE IF NOT EXISTS users 
                     (id INTEGER PRIMARY KEY, username TEXT UNIQUE, hashed_password TEXT)''')
        
        # 2. Automatically upgrade schema if it's an old database version
        try:
            db.execute("ALTER TABLE users ADD COLUMN email TEXT")
            db.execute("ALTER TABLE users ADD COLUMN disabled BOOLEAN")
        except sqlite3.OperationalError:
            # OperationalError means the columns already exist, which is safe to ignore
            pass 
            
        # 3. Create messages table for chat history
        db.execute('''CREATE TABLE IF NOT EXISTS messages 
                     (id INTEGER PRIMARY KEY, thread_id INTEGER, role TEXT, content TEXT, timestamp TIMESTAMP)''')
        db.commit()

def get_user(username):
    with get_user_db() as db:
        return db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

def create_user(username, hashed_password, email):
    try:
        with get_user_db() as db:
            # INSERT OR IGNORE prevents IntegrityError crashes if the user already exists
            db.execute(
                'INSERT OR IGNORE INTO users (username, hashed_password, email, disabled) VALUES (?, ?, ?, ?)', 
                (username, hashed_password, email, False)
            )
            db.commit()
    except Exception as e:
        print(f"Database error during user creation: {e}")

def search_quran_json(query_text, lang="en"):
    try:
        with open(QURAN_JSON, 'r', encoding='utf-8') as f:
            quran_data = json.load(f)
        
        lang_file = os.path.join(CHAPTERS_DIR, f"{lang}.json")
        with open(lang_file, 'r', encoding='utf-8') as f:
            chapters_data = json.load(f)

        results = []
        query_text = query_text.lower()
        
        for chapter in quran_data:
            chapter_id = chapter.get("id")
            chapter_name = next((c["name"] for c in chapters_data if c["id"] == chapter_id), f"Surah {chapter_id}")
            
            for verse in chapter.get("verses", []):
                if query_text in verse.get("text", "").lower():
                    results.append({"surah": chapter_name, "ayah": verse.get("id"), "text": verse.get("text")})
                if len(results) >= 3: break
            if len(results) >= 3: break
        return results
    except Exception as e:
        print(f"Error searching JSON: {e}")
        return []
