import sqlite3

USER_DB = "dev_bot_v2.db"

def get_user_db():
    conn = sqlite3.connect(USER_DB)
    conn.row_factory = sqlite3.Row
    return conn

def init_user_db():
    with get_user_db() as db:
        # Users Table
        db.execute('''CREATE TABLE IF NOT EXISTS users 
                     (id INTEGER PRIMARY KEY, username TEXT UNIQUE, hashed_password TEXT, email TEXT, disabled BOOLEAN)''')
        try:
            db.execute("ALTER TABLE users ADD COLUMN email TEXT")
            db.execute("ALTER TABLE users ADD COLUMN disabled BOOLEAN")
        except sqlite3.OperationalError:
            pass 
            
        # Threads and Messages Tables
        db.execute('''CREATE TABLE IF NOT EXISTS threads 
                     (id INTEGER PRIMARY KEY, username TEXT, title TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        db.execute('''CREATE TABLE IF NOT EXISTS messages 
                     (id INTEGER PRIMARY KEY, thread_id INTEGER, role TEXT, content TEXT, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        db.commit()

# --- User Management ---
def get_user(username):
    with get_user_db() as db:
        return db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()

def create_user(username, hashed_password, email):
    try:
        with get_user_db() as db:
            db.execute(
                'INSERT INTO users (username, hashed_password, email, disabled) VALUES (?, ?, ?, ?)', 
                (username, hashed_password, email, False)
            )
            db.commit()
            return True
    except sqlite3.IntegrityError:
        return False # Username already exists

# --- Chat History Management ---
def create_thread(username, title="New Chat"):
    with get_user_db() as db:
        cursor = db.execute('INSERT INTO threads (username, title) VALUES (?, ?)', (username, title))
        db.commit()
        return cursor.lastrowid

def get_threads(username):
    with get_user_db() as db:
        return db.execute('SELECT * FROM threads WHERE username = ? ORDER BY created_at DESC', (username,)).fetchall()

def get_messages(thread_id):
    with get_user_db() as db:
        rows = db.execute('SELECT role, content FROM messages WHERE thread_id = ? ORDER BY timestamp ASC', (thread_id,)).fetchall()
        return [{"role": row["role"], "content": row["content"]} for row in rows]

def add_message(thread_id, role, content):
    with get_user_db() as db:
        db.execute('INSERT INTO messages (thread_id, role, content) VALUES (?, ?, ?)', (thread_id, role, content))
        db.commit()

def clear_thread(thread_id):
    with get_user_db() as db:
        db.execute('DELETE FROM messages WHERE thread_id = ?', (thread_id,))
        db.commit()
