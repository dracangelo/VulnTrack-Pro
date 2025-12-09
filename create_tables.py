import sqlite3
import os

# Path to database
db_path = os.path.join(os.getcwd(), 'instance', 'vulntrack.db')

def create_tables():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("Creating teams table...")
    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS teams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL UNIQUE,
            description VARCHAR(255),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        print("Teams table created.")
    except Exception as e:
        print(f"Error creating teams table: {e}")

    print("Creating team_members association table...")
    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS team_members (
            team_id INTEGER,
            user_id INTEGER,
            FOREIGN KEY(team_id) REFERENCES teams(id),
            FOREIGN KEY(user_id) REFERENCES users(id),
            PRIMARY KEY (team_id, user_id)
        )
        ''')
        print("Team members table created.")
    except Exception as e:
        print(f"Error creating team_members table: {e}")
        
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_tables()
