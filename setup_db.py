import sqlite3

# Connect to (or create) the database
conn = sqlite3.connect("habits.db")
cursor = conn.cursor()

# Create the habits table
cursor.execute("""
CREATE TABLE IF NOT EXISTS habits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    habit_name TEXT,
    streak INTEGER DEFAULT 0,
    last_updated TEXT
)
""")

# Save and close
conn.commit()
conn.close()

print("✅ Database setup complete!")
