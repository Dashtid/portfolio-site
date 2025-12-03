"""
Database migration script to add missing columns to portfolio.db
"""

import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / "portfolio.db"


def get_table_columns(cursor, table_name):
    """Get list of column names for a table"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    return [row[1] for row in cursor.fetchall()]


def migrate_companies_table(conn):
    """Add missing columns to companies table"""
    cursor = conn.cursor()

    # Get existing columns
    existing_columns = get_table_columns(cursor, "companies")
    print(f"[*] Existing columns in companies table: {existing_columns}")

    # Define required columns with their SQL types
    required_columns = {
        "detailed_description": "TEXT",
        "video_url": "VARCHAR(500)",
        "video_title": "VARCHAR(255)",
        "map_url": "VARCHAR(500)",
        "map_title": "VARCHAR(255)",
        "responsibilities": "JSON",
        "technologies": "JSON",
    }

    # Add missing columns
    added_count = 0
    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            print(f"[+] Adding column: {column_name} ({column_type})")
            cursor.execute(f"ALTER TABLE companies ADD COLUMN {column_name} {column_type}")
            added_count += 1
        else:
            print(f"[v] Column already exists: {column_name}")

    if added_count > 0:
        conn.commit()
        print(f"[OK] Added {added_count} column(s) to companies table")
    else:
        print("[OK] No migration needed for companies table")

    return added_count


def migrate_projects_table(conn):
    """Add missing columns to projects table"""
    cursor = conn.cursor()

    # Get existing columns
    existing_columns = get_table_columns(cursor, "projects")
    print(f"\n[*] Existing columns in projects table: {existing_columns}")

    # Define required columns (based on model)
    required_columns = {
        "detailed_description": "TEXT",
        "video_url": "VARCHAR(500)",
        "video_title": "VARCHAR(255)",
        "map_url": "VARCHAR(500)",
        "map_title": "VARCHAR(255)",
        "responsibilities": "JSON",
        "technologies": "JSON",
        "github_url": "VARCHAR(500)",
    }

    # Add missing columns
    added_count = 0
    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            print(f"[+] Adding column: {column_name} ({column_type})")
            cursor.execute(f"ALTER TABLE projects ADD COLUMN {column_name} {column_type}")
            added_count += 1
        else:
            print(f"[v] Column already exists: {column_name}")

    if added_count > 0:
        conn.commit()
        print(f"[OK] Added {added_count} column(s) to projects table")
    else:
        print("[OK] No migration needed for projects table")

    return added_count


def main():
    """Execute database migrations"""
    print(f"[*] Starting database migration for: {DATABASE_PATH}")

    if not DATABASE_PATH.exists():
        print(f"[-] ERROR: Database file not found at {DATABASE_PATH}")
        return 1

    try:
        # Connect to database
        conn = sqlite3.connect(DATABASE_PATH)

        # Migrate companies table
        companies_added = migrate_companies_table(conn)

        # Migrate projects table
        projects_added = migrate_projects_table(conn)

        # Close connection
        conn.close()

        total_added = companies_added + projects_added
        if total_added > 0:
            print(f"\n[OK] Migration complete! Added {total_added} column(s) total")
        else:
            print("\n[OK] Database schema is up to date")

    except Exception as e:
        print(f"[-] ERROR during migration: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return 1
    else:
        return 0


if __name__ == "__main__":
    exit(main())
