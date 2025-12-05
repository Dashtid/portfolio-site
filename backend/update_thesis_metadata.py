"""
Update Document Metadata

Script to update thesis titles and descriptions to match original portfolio-site.
"""

import sqlite3
from pathlib import Path

# Database path
DB_PATH = Path("portfolio.db")

# Updated document metadata
UPDATES = [
    {
        "file_path": "static/documents/bachelor-thesis.pdf",
        "title": "Bachelor's Thesis: Development of a User-friendly Method of Processing Data from Ergonomics Measurements Utilizing Inclinometers",
        "description": "Bachelor's Thesis in Biomedical Engineering focusing on ergonomics data processing and inclinometer measurements for improved workplace safety analysis.",
    },
    {
        "file_path": "static/documents/master-thesis.pdf",
        "title": "Master's Thesis: Improving Quality Assurance of Radiology Equipment Using Process Modelling and Multi-actor System Analysis",
        "description": "Master's Thesis in Biomedical Engineering - Computer Science. Conducted at SoftPro Medical Solutions, integrating Medusa inventory management with radiology workflows and optimizing quality assurance processes for medical equipment.",
    },
]


def main():
    """Update document metadata in database"""
    if not DB_PATH.exists():
        print(f"[!] Database not found: {DB_PATH}")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    for update in UPDATES:
        cursor.execute(
            """
            UPDATE documents
            SET title = ?, description = ?
            WHERE file_path = ?
        """,
            (update["title"], update["description"], update["file_path"]),
        )

        print(f"[+] Updated: {update['file_path']}")
        print(f"    Title: {update['title'][:60]}...")

    conn.commit()

    # Verify updates
    print("\n[i] Verifying updates:")
    cursor.execute("SELECT title, file_size FROM documents ORDER BY published_date")
    for title, size in cursor.fetchall():
        print(f"  - {title[:60]}... ({size / 1024 / 1024:.1f} MB)")

    conn.close()
    print("\n[OK] Document metadata updated successfully")


if __name__ == "__main__":
    main()
