import sqlite3
from models import DB_FILE

def get_db():
    return sqlite3.connect(DB_FILE)

def add_expense(user_id, amount, currency, converted_amount,
                base_currency, category, date, notes):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''INSERT INTO expenses
        (user_id, amount, currency, converted_amount, base_currency, category, date, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
        (user_id, amount, currency, converted_amount, base_currency, category, date, notes))
    conn.commit()
    conn.close()

def list_expenses(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM expenses WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    cols = [c[0] for c in cur.description]
    conn.close()
    return [dict(zip(cols, row)) for row in rows]

def get_expense(expense_id, user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM expenses WHERE id = ? AND user_id = ?", (expense_id, user_id))
    row = cur.fetchone()
    if row:
        cols = [c[0] for c in cur.description]
        return dict(zip(cols, row))
    return None

def update_expense(expense_id, user_id, amount, currency, converted_amount,
                   base_currency, category, date, notes):
    conn = get_db()
    cur = conn.cursor()
    cur.execute('''UPDATE expenses
        SET amount=?, currency=?, converted_amount=?, base_currency=?, category=?, date=?, notes=?
        WHERE id=? AND user_id=?''',
        (amount, currency, converted_amount, base_currency, category, date, notes, expense_id, user_id))
    conn.commit()
    conn.close()

def delete_expense(expense_id, user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE id=? AND user_id=?", (expense_id, user_id))
    conn.commit()
    conn.close()

def delete_all_expenses(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM expenses WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
