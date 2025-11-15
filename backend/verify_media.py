"""Quick script to verify media URLs in database"""
import asyncio
from app.database import AsyncSessionLocal
from app.models.company import Company
from sqlalchemy import select

async def main():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Company.name, Company.video_url, Company.map_url)
            .order_by(Company.name)
        )

        print("Company Media Status:")
        print("-" * 70)
        for row in result:
            name = row[0]
            has_video = "Yes" if row[1] else "No"
            has_map = "Yes" if row[2] else "No"
            print(f"{name:40} Video: {has_video:3}  Map: {has_map:3}")

if __name__ == "__main__":
    asyncio.run(main())
