"""Migrate real content - Quick fix with date objects"""
import asyncio, sys
from pathlib import Path
from datetime import date
sys.path.append(str(Path(__file__).parent))
from app.database import AsyncSessionLocal
from app.models.company import Company
from app.models.education import Education
from sqlalchemy import delete

async def main():
    async with AsyncSessionLocal() as db:
        # Clear
        await db.execute(delete(Company))
        await db.execute(delete(Education))
        await db.commit()
        print("[+] Cleared")
        
        # Add companies with date objects
        db.add(Company(name="Hermes Medical Solutions", title="QA/RA & Security Specialist", 
                      description="QA/RA & Security Specialist ensuring NIS2/ISO 27001 compliance",
                      location="Stockholm, Sweden", start_date=date(2022,1,1), end_date=None, 
                      website="https://hermesmedical.com", order_index=1))
        db.add(Company(name="Scania Engines", title="Engineering Role",
                      description="Troubleshooting and documentation at Scania Södertälje",
                      location="Södertälje, Sweden", start_date=date(2020,1,1), end_date=date(2021,12,31),
                      website="https://www.scania.com", order_index=2))
        db.add(Company(name="Finnish Defence Forces", title="Platoon Leader (2nd Lieutenant)",
                      description="Marine commandos, command of 150 soldiers",
                      location="Finland", start_date=date(2018,6,1), end_date=date(2019,6,1), order_index=3))
        await db.commit()
        print("[+] Added 3 companies (sample)")
        
        # Add education with 'order' field  
        db.add(Education(institution="Lund University", degree="Bachelor of Science - BS",
                        field_of_study="Biomedical Engineering", start_date=date(2011,9,1),
                        end_date=date(2014,6,1), order=1))
        db.add(Education(institution="KTH Royal Institute of Technology", degree="Master of Science - MS",
                        field_of_study="Biomedical Engineering - Computer Science", 
                        start_date=date(2014,9,1), end_date=date(2016,6,1), order=2))
        await db.commit()
        print("[+] Added 2 education entries")
    print("[+] Done! Check: curl http://localhost:8001/api/v1/companies/")

if __name__ == "__main__":
    asyncio.run(main())
