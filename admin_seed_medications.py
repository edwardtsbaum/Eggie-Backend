import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from utils.seed_medications import seed_medication_dictionary

async def admin_seed_medications():
    """Admin function to seed medications - run locally or on admin panel."""
    print("Starting admin medication seeding...")
    try:
        await seed_medication_dictionary()
        print("✅ Medications seeded successfully!")
        print("📱 All mobile users will now see these medications")
    except Exception as e:
        print(f"❌ Error seeding medications: {e}")

if __name__ == "__main__":
    asyncio.run(admin_seed_medications())
