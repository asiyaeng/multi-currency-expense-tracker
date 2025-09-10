import sqlite3
import bcrypt
from models import DB_FILE

def register_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    try:
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        cur.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, hashed))
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, "Username already exists"
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT id, username, password_hash FROM users WHERE username=?", (username,))
    row = cur.fetchone()
    conn.close()
    if row:
        uid, uname, pwhash = row
        if bcrypt.checkpw(password.encode(), pwhash.encode()):
            return True, {"id": uid, "username": uname}
    return False, "Invalid credentials"

def change_password(user_id, old_password, new_password):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("SELECT password_hash FROM users WHERE id=?", (user_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        return False, "User not found"
    old_hash = row[0]
    if not bcrypt.checkpw(old_password.encode(), old_hash.encode()):
        conn.close()
        return False, "Old password is incorrect"
    new_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()
    cur.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, user_id))
    conn.commit()
    conn.close()
    return True, None

def delete_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
