import sqlite3

conn = sqlite3.connect("subscription_users.db")
cursor = conn.cursor()

# Add trial_count column if not exists
try:
    cursor.execute("ALTER TABLE users ADD COLUMN trial_count INTEGER DEFAULT 0")
    print("✅ Column trial_count added.")
except Exception as e:
    print("⚠️ Column might already exist:", e)

conn.commit()
conn.close()
