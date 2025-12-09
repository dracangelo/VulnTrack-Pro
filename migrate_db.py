import sqlite3
import os

# Database file path
DB_FILE = 'instance/vulntrack.db'

if not os.path.exists(DB_FILE):
    print(f"Database file {DB_FILE} not found.")
    exit(1)

print(f"Migrating database: {DB_FILE}")

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

try:
    # Check if column exists
    cursor.execute("PRAGMA table_info(target_groups)")
    columns = [info[1] for info in cursor.fetchall()]
    
    if 'team_id' in columns:
        print("Column 'team_id' already exists in 'target_groups'.")
    else:
        print("Adding column 'team_id' to 'target_groups'...")
        cursor.execute("ALTER TABLE target_groups ADD COLUMN team_id INTEGER REFERENCES teams(id)")
        conn.commit()
        print("Migration successful.")

except Exception as e:
    print(f"Migration failed: {e}")
finally:
    conn.close()
