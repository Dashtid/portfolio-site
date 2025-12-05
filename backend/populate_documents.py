"""
Populate Documents Table

Script to populate the documents table with academic thesis PDFs.
"""

import sqlite3
import uuid
from pathlib import Path

# Database path
DB_PATH = "portfolio.db"
STATIC_DIR = Path("static/documents")

# Get file sizes
bachelor_path = STATIC_DIR / "bachelor-thesis.pdf"
master_path = STATIC_DIR / "master-thesis.pdf"

bachelor_size = bachelor_path.stat().st_size if bachelor_path.exists() else 1365000  # ~1.3 MB
master_size = master_path.stat().st_size if master_path.exists() else 4200000  # ~4.0 MB

# Document data
DOCUMENTS = [
    {
        "id": str(uuid.uuid4()),
        "title": "Bachelor Thesis: Network Security Analysis",
        "description": "Comprehensive analysis of network security protocols and vulnerabilities in modern enterprise environments. Focused on intrusion detection systems and firewall configurations.",
        "document_type": "thesis",
        "file_path": "static/documents/bachelor-thesis.pdf",
        "file_size": bachelor_size,
        "file_url": "http://localhost:8001/static/documents/bachelor-thesis.pdf",
        "published_date": "2015-06-15",
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Master Thesis: Cloud Security in Healthcare Systems",
        "description": "In-depth study of cloud security challenges in healthcare information systems, including HIPAA compliance, data encryption, and access control mechanisms. Proposed framework for secure cloud-based electronic health records.",
        "document_type": "thesis",
        "file_path": "static/documents/master-thesis.pdf",
        "file_size": master_size,
        "file_url": "http://localhost:8001/static/documents/master-thesis.pdf",
        "published_date": "2017-05-20",
    },
]


def main():
    """Populate documents table"""
    db_path = Path(DB_PATH)
    if not db_path.exists():
        print(f"[!] Database not found: {DB_PATH}")
        print("[i] Please run the FastAPI server first to create the database")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create documents table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            document_type TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            file_url TEXT NOT NULL,
            published_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Clear existing documents
    cursor.execute("DELETE FROM documents")
    print("[i] Cleared existing documents")

    # Insert new documents
    for doc in DOCUMENTS:
        cursor.execute(
            """
            INSERT INTO documents (
                id, title, description, document_type, file_path,
                file_size, file_url, published_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                doc["id"],
                doc["title"],
                doc["description"],
                doc["document_type"],
                doc["file_path"],
                doc["file_size"],
                doc["file_url"],
                doc["published_date"],
            ),
        )
        print(f"[+] Added: {doc['title']} ({doc['file_size'] / 1024 / 1024:.1f} MB)")

    conn.commit()
    conn.close()

    print(f"\n[OK] Successfully populated {len(DOCUMENTS)} documents")
    print("[i] Documents are now available at http://localhost:8001/api/v1/documents/")


if __name__ == "__main__":
    main()
