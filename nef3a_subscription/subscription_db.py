import sqlite3
from datetime import datetime, timedelta

DB_NAME = "subscription_users.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            trial_count INTEGER DEFAULT 0,
            subscription_start TEXT,
            subscription_end TEXT,
            status TEXT DEFAULT 'inactive'
        )
    """)
    conn.commit()
    conn.close()

def init_payment_table():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            plan TEXT,
            amount REAL,
            tx_id TEXT UNIQUE,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_trial_count(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT trial_count FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

def increment_trial(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cursor.execute("UPDATE users SET trial_count = trial_count + 1, status = 'trial' WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def can_use_trial(user_id):
    return get_trial_count(user_id) < 3  # now allows 3 trials

def reset_trial(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET trial_count = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def activate_subscription(user_id, days=30):
    now = datetime.now()
    sub_end = now + timedelta(days=days)
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    cursor.execute("""
        UPDATE users
        SET subscription_start = ?, subscription_end = ?, status = 'active'
        WHERE user_id = ?
    """, (now.isoformat(), sub_end.isoformat(), user_id))
    conn.commit()
    conn.close()

def is_user_active(user_id):
    user = get_user(user_id)
    if not user:
        return False
    sub_end = datetime.fromisoformat(user[3]) if user[3] else None
    return sub_end and sub_end > datetime.now()

def revoke_expired_subscriptions():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        UPDATE users
        SET status = 'inactive'
        WHERE subscription_end IS NOT NULL
        AND subscription_end < ?
        AND status = 'active'
    """, (now,))
    conn.commit()
    conn.close()

def record_payment(user_id, plan, amount, tx_id, timestamp):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO payments (user_id, plan, amount, tx_id, timestamp)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, plan, amount, tx_id, timestamp))
        conn.commit()
    except sqlite3.IntegrityError:
        print(f"⚠️ Payment with tx_id {tx_id} already recorded.")
    conn.close()
