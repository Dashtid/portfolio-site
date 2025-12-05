"""
Populate PostgreSQL database with Documents (Theses) data

This script populates the production PostgreSQL database on Fly.io with
academic thesis documents.

Run on Fly.io:
    flyctl ssh console -a dashti-portfolio-backend
    cd /app
    python populate_documents_postgres.py
"""

import asyncio
import sys
import uuid
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import delete, select

from app.database import AsyncSessionLocal
from app.models.document import Document

# Production backend URL
BACKEND_URL = "https://dashti-portfolio-backend.fly.dev"

# Document data - actual file sizes from local files
# bachelor-thesis.pdf: 1,287,356 bytes (1.23 MB)
# master-thesis.pdf: 4,094,388 bytes (3.90 MB)
DOCUMENTS_DATA = [
    {
        "id": str(uuid.uuid4()),
        "title": "Bachelor Thesis: Development of a User-friendly Method of Processing Data from Ergonomics Measurements Utilizing Inclinometers",
        "description": "Research project at Lund University focusing on developing user-friendly data processing methods for ergonomics measurements using inclinometer sensors. The thesis explores practical applications in occupational health and workplace ergonomics assessment.",
        "document_type": "thesis",
        "file_path": "static/documents/bachelor-thesis.pdf",
        "file_size": 1287356,  # 1.23 MB
        "file_url": f"{BACKEND_URL}/static/documents/bachelor-thesis.pdf",
        "published_date": "2015-06-15",
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Master Thesis: Improving Quality Assurance of Radiology Equipment Using Process Modelling and Multi-actor System Analysis",
        "description": "Research conducted at KTH Royal Institute of Technology in collaboration with SoftPro Medical Solutions. The thesis investigates methods to improve QA processes for radiology equipment through process modelling techniques and multi-actor system analysis, contributing to enhanced medical device quality management.",
        "document_type": "thesis",
        "file_path": "static/documents/master-thesis.pdf",
        "file_size": 4094388,  # 3.90 MB
        "file_url": f"{BACKEND_URL}/static/documents/master-thesis.pdf",
        "published_date": "2020-06-15",
    },
]


async def populate_documents():
    """Populate documents table with thesis data"""

    print("=" * 70)
    print("PostgreSQL Documents Population Script")
    print("=" * 70)
    print()

    async with AsyncSessionLocal() as db:
        # Check current count
        result = await db.execute(select(Document))
        existing = result.scalars().all()
        print(f"[INFO] Current documents in database: {len(existing)}")

        # Clear existing documents
        if existing:
            print("[INFO] Clearing existing documents...")
            await db.execute(delete(Document))
            await db.commit()
            print("[OK] Cleared existing documents")

        # Insert new documents
        print()
        print("[INFO] Inserting documents...")
        print("-" * 70)

        for doc_data in DOCUMENTS_DATA:
            document = Document(
                id=doc_data["id"],
                title=doc_data["title"],
                description=doc_data["description"],
                document_type=doc_data["document_type"],
                file_path=doc_data["file_path"],
                file_size=doc_data["file_size"],
                file_url=doc_data["file_url"],
                published_date=doc_data["published_date"],
            )
            db.add(document)
            size_mb = doc_data["file_size"] / 1024 / 1024
            print(f"  [+] {doc_data['title'][:50]}... ({size_mb:.2f} MB)")

        await db.commit()
        print("-" * 70)
        print()

        # Verification
        result = await db.execute(select(Document))
        documents = result.scalars().all()

        print("=" * 70)
        print("Verification - Documents in database:")
        print("-" * 70)
        for doc in documents:
            size_mb = doc.file_size / 1024 / 1024
            print(f"  - {doc.title[:60]}...")
            print(
                f"    Type: {doc.document_type} | Size: {size_mb:.2f} MB | Date: {doc.published_date}"
            )
            print(f"    URL: {doc.file_url}")
            print()
        print("-" * 70)
        print(f"Total: {len(documents)} documents")
        print("=" * 70)
        print()
        print("[SUCCESS] Documents populated successfully!")
        print("API endpoint: /api/v1/documents/")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(populate_documents())
