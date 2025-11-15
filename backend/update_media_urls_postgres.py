"""
Update PostgreSQL database with media URLs (YouTube videos and Google Maps)

This script updates the production PostgreSQL database on Fly.io with
video_url, video_title, map_url, and map_title for all companies.

Run on Fly.io:
    flyctl ssh console -a dashti-portfolio-backend
    cd /app
    python update_media_urls_postgres.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, update
from app.database import AsyncSessionLocal
from app.models.company import Company


# Media content extracted from original dashti.se site
MEDIA_DATA = {
    "Hermes Medical Solutions": {
        "video_url": "https://www.youtube.com/embed/bdbevZrjdtU",
        "video_title": "HERMIA – ALL-IN-ONE Molecular Imaging Software",
        "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d23019.922985510006!2d17.999845284557612!3d59.338079926240894!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f77fcd4b7b5e1%3A0xf7dcf06b9ce62c50!2sHermes%20Medical%20Solutions%20AB!5e0!3m2!1ssv!2sse!4v1749928857261!5m2!1ssv!2sse",
        "map_title": "Hermes Medical Solutions AB Location",
    },
    "Karolinska University Hospital": {
        "video_url": "https://www.youtube.com/embed/05k9c4zPBWo",
        "video_title": "Karolinska University Hospital - Research and Innovation",
        "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d27373.793052339282!2d18.003493380951838!3d59.34014358751482!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f9d5fc509b8cd%3A0x6f2520b3e07808ba!2sKarolinska%20Universitetssjukhuset%20Solna!5e0!3m2!1ssv!2sse!4v1749832921700!5m2!1ssv!2sse",
        "map_title": "Karolinska University Hospital Solna Location",
    },
    "Philips AB": {
        "video_url": "https://www.youtube.com/embed/i2wsMvBen1c",
        "video_title": "Philips Healthcare Innovation",
        "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d32535.951427291504!2d17.999412838149354!3d59.35804439018847!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f9e93436d98c5%3A0x16230b74d42df0ca!2sPhilips%20AB!5e0!3m2!1ssv!2sse!4v1749928636549!5m2!1ssv!2sse",
        "map_title": "Philips AB Stockholm Location",
    },
    "Scania": {
        "video_url": "https://www.youtube.com/embed/Rm6grXvyX6I",
        "video_title": "Scania Truck Manufacturing Process",
        "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d130603.48820521029!2d17.67627411091932!3d59.238085496816325!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f12baeb6eae75%3A0x16a5832b5a283d07!2zU0NBTklBIFPDtmRlcnTDpGxqZQ!5e0!3m2!1ssv!2sse!4v1749832105161!5m2!1ssv!2sse",
        "map_title": "Scania Södertälje Location",
    },
    "Finnish Defence Forces - Nyland Brigade": {
        "video_url": "https://www.youtube.com/embed/AcLYbg2Jk9c?si=LFG4nBnqCZ3WRfSt",
        "video_title": "Finnish Defence Forces - Nyland Brigade",
        "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d720002.5239741812!2d22.654854775421864!3d60.10216545447512!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x468da9e761c88d0f%3A0x8809aeeec13b380b!2sNyland%20Brigade!5e0!3m2!1ssv!2sse!4v1749150985148!5m2!1ssv!2sse",
        "map_title": "Nyland Brigade Location - Dragsvik, Finland",
    },
    "Södersjukhuset - SÖS": {
        "video_url": None,  # SÖS page only has a map, no video
        "video_title": None,
        "map_url": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d38737.84701537516!2d18.003017736901185!3d59.31780499604735!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x465f77ec1b565595%3A0x4f818c747249a764!2sS%C3%B6dersjukhuset!5e0!3m2!1ssv!2sse!4v1749832781009!5m2!1ssv!2sse",
        "map_title": "Södersjukhuset Location - Stockholm",
    },
    # SoftPro Medical Solutions has no media content (thesis-only entry)
}


async def update_media_urls():
    """Update all companies with their media URLs"""

    print("=" * 70)
    print("PostgreSQL Media URL Update Script")
    print("=" * 70)
    print()

    async with AsyncSessionLocal() as db:
        updated_count = 0
        not_found = []

        for company_name, media in MEDIA_DATA.items():
            print(f"Updating: {company_name}")

            # Check if company exists
            result = await db.execute(
                select(Company).where(Company.name == company_name)
            )
            company = result.scalar_one_or_none()

            if not company:
                print(f"  [WARN] Company not found: {company_name}")
                not_found.append(company_name)
                continue

            # Update media URLs
            company.video_url = media["video_url"]
            company.video_title = media["video_title"]
            company.map_url = media["map_url"]
            company.map_title = media["map_title"]

            await db.commit()
            updated_count += 1

            print(f"  [OK] Updated successfully")
            print(f"    - Video: {'Yes' if media['video_url'] else 'No'}")
            print(f"    - Map: {'Yes' if media['map_url'] else 'No'}")
            print()

        # Summary
        print("=" * 70)
        print("Summary:")
        print(f"  - Companies updated: {updated_count}/{len(MEDIA_DATA)}")
        if not_found:
            print(f"  - Not found: {', '.join(not_found)}")
        print("=" * 70)
        print()

        # Verification query
        print("Verification - Companies with media:")
        print("-" * 70)

        result = await db.execute(
            select(Company).order_by(Company.name)
        )
        companies = result.scalars().all()

        for company in companies:
            has_video = "Yes" if company.video_url else "No"
            has_map = "Yes" if company.map_url else "No"
            print(f"{company.name:40} Video: {has_video:3}  Map: {has_map:3}")

        print("=" * 70)
        print("[SUCCESS] Media URLs updated successfully!")
        print("=" * 70)


if __name__ == "__main__":
    asyncio.run(update_media_urls())
