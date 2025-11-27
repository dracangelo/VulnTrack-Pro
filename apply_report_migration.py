#!/usr/bin/env python3
"""
Simple migration script to add report columns to scans table
"""
import sqlite3
import sys

def run_migration():
    try:
        conn = sqlite3.connect('vulntrack.db')
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(scans)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'report_html' in columns and 'report_pdf' in columns:
            print("✅ Migration already applied - report columns exist")
            return True
            
        # Add the columns
        print("Adding report_html column...")
        cursor.execute("ALTER TABLE scans ADD COLUMN report_html TEXT")
        
        print("Adding report_pdf column...")
        cursor.execute("ALTER TABLE scans ADD COLUMN report_pdf BLOB")
        
        conn.commit()
        print("✅ Migration completed successfully!")
        print("   - Added report_html (TEXT)")
        print("   - Added report_pdf (BLOB)")
        
        conn.close()
        return True
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("✅ Columns already exist - migration not needed")
            return True
        else:
            print(f"❌ Error: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1)
