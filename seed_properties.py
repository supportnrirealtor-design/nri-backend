import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
db_name = os.environ['DB_NAME']

properties = [
    {
        "id": str(uuid.uuid4()),
        "title": "Brigade Utopia - Luxury Apartment",
        "price": "₹1.2 Cr",
        "location": "Whitefield, Bangalore",
        "property_type": "Apartment",
        "bedrooms": "3",
        "area": "1850 sqft",
        "description": "Spacious 3BHK luxury apartment with modern amenities, landscaped gardens, and premium finishes. Perfect for families seeking comfort and style.",
        "images": [
            "https://images.unsplash.com/photo-1757439402296-000be181e38b?q=85",
            "https://images.unsplash.com/photo-1738168273959-952fdc961991?q=85"
        ],
        "featured": True,
        "status": "Available",
        "builder": "Brigade",
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Shobha Dream Acres - Premium Villa",
        "price": "₹3.5 Cr",
        "location": "Balagere, Bangalore",
        "property_type": "Villa",
        "bedrooms": "4",
        "area": "3200 sqft",
        "description": "Exquisite 4BHK villa with private garden, premium interiors, and world-class amenities. Experience luxury living at its finest.",
        "images": [
            "https://images.unsplash.com/photo-1767950470198-c9cd97f8ed87?q=85",
            "https://images.pexels.com/photos/7031708/pexels-photo-7031708.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940"
        ],
        "featured": True,
        "status": "Available",
        "builder": "Shobha",
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Concorde Cupola - Sky Penthouse",
        "price": "₹5.8 Cr",
        "location": "Hebbal, Bangalore",
        "property_type": "Penthouse",
        "bedrooms": "5",
        "area": "4500 sqft",
        "description": "Ultra-luxurious penthouse with panoramic city views, private terrace, and bespoke interiors. The pinnacle of sophisticated living.",
        "images": [
            "https://images.unsplash.com/photo-1757439402375-2f2a4ab0dc75?q=85",
            "https://images.unsplash.com/photo-1638454795595-0a0abf68614d?q=85"
        ],
        "featured": True,
        "status": "Available",
        "builder": "Concorde",
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Royal Indraprastha - Elite Residence",
        "price": "₹2.8 Cr",
        "location": "Yelahanka, Bangalore",
        "property_type": "Apartment",
        "bedrooms": "4",
        "area": "2800 sqft",
        "description": "Premium 4BHK apartment with state-of-the-art facilities, clubhouse, and serene environment. Royal living redefined.",
        "images": [
            "https://images.pexels.com/photos/6970049/pexels-photo-6970049.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
            "https://images.unsplash.com/photo-1757439402268-1da284675170?q=85"
        ],
        "featured": True,
        "status": "Available",
        "builder": "Royal Indraprastha",
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Brigade Gateway - Modern Living",
        "price": "₹95 Lakhs",
        "location": "Rajajinagar, Bangalore",
        "property_type": "Apartment",
        "bedrooms": "2",
        "area": "1250 sqft",
        "description": "Contemporary 2BHK apartment with smart home features and premium amenities. Perfect starter home for young professionals.",
        "images": [
            "https://images.unsplash.com/photo-1738168273959-952fdc961991?q=85"
        ],
        "featured": False,
        "status": "Available",
        "builder": "Brigade",
        "created_at": datetime.now(timezone.utc).isoformat()
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Shobha Silicon Oasis - Tech Hub Villa",
        "price": "₹4.2 Cr",
        "location": "Hosa Road, Bangalore",
        "property_type": "Villa",
        "bedrooms": "4",
        "area": "3600 sqft",
        "description": "Stunning villa in the heart of Bangalore's tech corridor. Features include smart automation, private pool, and landscaped gardens.",
        "images": [
            "https://images.pexels.com/photos/7031708/pexels-photo-7031708.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940"
        ],
        "featured": False,
        "status": "Available",
        "builder": "Shobha",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
]

async def seed_database():
    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]
    
    # Clear existing properties
    await db.properties.delete_many({})
    print("Cleared existing properties")
    
    # Insert new properties
    await db.properties.insert_many(properties)
    print(f"Successfully seeded {len(properties)} properties")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
