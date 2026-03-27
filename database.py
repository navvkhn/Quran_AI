import json
import sqlite3
import os
from datetime import datetime

USER_DB = "dev_bot_v2.db"
QURAN_JSON = "quran.json"
CHAPTERS_DIR = "chapters"

def init_user_db():
    conn = sqlite3.connect(USER_DB)
    db = conn.cursor()
    db.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id INTEGER PRIMARY KEY, username TEXT UNIQUE, hashed_password TEXT)''')
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect(USER_DB)
    conn.row_factory = sqlite3.Row
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()
    return user

def search_quran_json(query_text, lang="en"):
    """Searches quran.json and chapter name files."""
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
            # Cross-reference chapter name from translation file
            chapter_name = next((c["name"] for c in chapters_data if c["id"] == chapter_id), f"Surah {chapter_id}")
            
            for verse in chapter.get("verses", []):
                if query_text in verse.get("text", "").lower():
                    results.append({
                        "surah": chapter_name,
                        "ayah": verse.get("id"),
                        "text": verse.get("text")
                    })
                if len(results) >= 3: break
            if len(results) >= 3: break
        return results
    except Exception:
        return []
