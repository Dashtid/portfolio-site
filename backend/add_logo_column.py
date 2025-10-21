"""
Quick script to add logo_url column to education table
"""
import sqlite3

# Connect to database
conn = sqlite3.connect('portfolio.db')
cursor = conn.cursor()

try:
    # Add logo_url column to education table
    cursor.execute("ALTER TABLE education ADD COLUMN logo_url VARCHAR(500);")
    conn.commit()
    print("[+] Successfully added logo_url column to education table")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e).lower():
        print("[!] logo_url column already exists")
    else:
        print(f"[-] Error: {e}")
finally:
    conn.close()
