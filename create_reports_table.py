#!/usr/bin/env python3
"""
Migration script to create reports table
"""
import sqlite3
import sys
import os

def run_migration():
    try:
        # Use the instance database path
        db_path = 'instance/vulntrack.db'
        if not os.path.exists(db_path):
            print(f"❌ Database not found at {db_path}")
            return False
            
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='reports'")
        if cursor.fetchone():
            print("✅ Table 'reports' already exists")
            conn.close()
            return True
            
        # Create the table
        print("Creating reports table...")
        cursor.execute("""
        CREATE TABLE reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(255) NOT NULL,
            type VARCHAR(50) NOT NULL,
            format VARCHAR(10) NOT NULL,
            status VARCHAR(50) DEFAULT 'pending',
            created_at DATETIME,
            scan_id INTEGER,
            file_path VARCHAR(512),
            content TEXT,
            pdf_content BLOB,
            FOREIGN KEY(scan_id) REFERENCES scans(id)
        )
        """)
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
