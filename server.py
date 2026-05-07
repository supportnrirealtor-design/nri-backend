import cloudinary
import cloudinary.uploader
from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import requests as http_requests

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
db_name = os.environ.get('DB_NAME', 'nri_realtor')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Object Storage
STORAGE_URL = "https://integrations.emergentagent.com/objstore/api/v1/storage"
EMERGENT_KEY = os.environ.get("EMERGENT_LLM_KEY")
APP_NAME = "nri-realtor"
storage_key = None

def init_storage():
    global storage_key
    if storage_key:
        return storage_key
    if not EMERGENT_KEY:
        raise HTTPException(status_code=500, detail="Storage not configured")
    resp = http_requests.post(f"{STORAGE_URL}/init", json={"emergent_key": EMERGENT_KEY}, timeout=30)
    resp.raise_for_status()
    storage_key = resp.json()["storage_key"]
    return storage_key

def put_object(path: str, data: bytes, content_type: str) -> dict:
    key = init_storage()
    resp = http_requests.put(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key, "Content-Type": content_type},
        data=data, timeout=120
    )
    resp.raise_for_status()
    return resp.json()

def get_object(path: str):
    key = init_storage()
    resp = http_requests.get(
        f"{STORAGE_URL}/objects/{path}",
        headers={"X-Storage-Key": key}, timeout=60
    )
    resp.raise_for_status()
    return resp.content, resp.headers.get("Content-Type", "application/octet-stream")

# Create the main app
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# LeadRat CRM
LEADRAT_API_URL = "https://connect.leadrat.com/api/v1/integration/GoogleAds"
LEADRAT_API_KEY = os.environ.get("LEADRAT_API_KEY")

# Models
class Enquiry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    enquiry_type: str
    name: str
    phone: str
    location: str
    property_type: str
    budget: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    leadrat_synced: bool = False

class EnquiryCreate(BaseModel):
    enquiry_type: str
    name: str
    phone: str
    location: str
    property_type: str
    budget: str

class Property(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    price: str
    location: str
    property_type: str
    bedrooms: str
    area: str
    description: str
    images: List[str] = []
    featured: bool = False
    status: str = "Available"
    builder: Optional[str] = None
    pricing_range: Optional[str] = None
    land_area: Optional[str] = None
    units: Optional[str] = None
    carpet_area: Optional[str] = None
    balcony_area: Optional[str] = None
    video_url: Optional[str] = None
    brochure_url: Optional[str] = None
    pricing_pdf_url: Optional[str] = None
    connectivity: Optional[str] = None
    content_type: str = "listing"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PropertyCreate(BaseModel):
    title: str
    price: str = ""
    location: str = ""
    property_type: str = ""
    bedrooms: str = ""
    area: str = ""
    description: str = ""
    images: List[str] = []
    featured: bool = False
    status: str = "Available"
    builder: Optional[str] = None
    pricing_range: Optional[str] = None
    land_area: Optional[str] = None
    units: Optional[str] = None
    carpet_area: Optional[str] = None
    balcony_area: Optional[str] = None
    video_url: Optional[str] = None
    brochure_url: Optional[str] = None
    pricing_pdf_url: Optional[str] = None
    connectivity: Optional[str] = None
    content_type: str = "listing"

class PropertyUpdate(BaseModel):
    title: Optional[str] = None
    price: Optional[str] = None
    location: Optional[str] = None
    property_type: Optional[str] = None
    bedrooms: Optional[str] = None
    area: Optional[str] = None
    description: Optional[str] = None
    images: Optional[List[str]] = None
    featured: Optional[bool] = None
    status: Optional[str] = None
    builder: Optional[str] = None
    pricing_range: Optional[str] = None
    land_area: Optional[str] = None
    units: Optional[str] = None
    carpet_area: Optional[str] = None
    balcony_area: Optional[str] = None
    video_url: Optional[str] = None
    brochure_url: Optional[str] = None
    pricing_pdf_url: Optional[str] = None
    connectivity: Optional[str] = None
    content_type: Optional[str] = None

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None

# Routes
@api_router.get("/")
async def root():
    return {"message": "The NRI Realtor API"}

@api_router.post("/admin/login", response_model=AdminLoginResponse)
async def admin_login(credentials: AdminLogin):
    if credentials.username == "NRI.admin" and credentials.password == "integrity that truly matters":
        return AdminLoginResponse(success=True, message="Login successful", token="admin-token-123")
    raise HTTPException(status_code=401, detail="Invalid credentials")

@api_router.get("/properties", response_model=List[Property])
async def get_properties(featured: Optional[bool] = None, status: Optional[str] = None, builder: Optional[str] = None):
    query = {}
    if featured is not None:
        query['featured'] = featured
    if status:
        query['status'] = status
    if builder:
        query['builder'] = builder
    properties = await db.properties.find(query, {"_id": 0}).to_list(1000)
    for prop in properties:
        if isinstance(prop.get('created_at'), str):
            prop['created_at'] = datetime.fromisoformat(prop['created_at'])
    return properties

@api_router.get("/properties/{property_id}", response_model=Property)
async def get_property(property_id: str):
    prop = await db.properties.find_one({"id": property_id}, {"_id": 0})
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if isinstance(prop.get('created_at'), str):
        prop['created_at'] = datetime.fromisoformat(prop['created_at'])
    return prop

@api_router.post("/properties", response_model=Property, status_code=201)
async def create_property(property_data: PropertyCreate):
    property_obj = Property(**property_data.model_dump())
    doc = property_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.properties.insert_one(doc)
    return property_obj

@api_router.put("/properties/{property_id}", response_model=Property)
async def update_property(property_id: str, property_data: PropertyUpdate):
    existing = await db.properties.find_one({"id": property_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Property not found")
    update_data = {k: v for k, v in property_data.model_dump().items() if v is not None}
    if update_data:
        await db.properties.update_one({"id": property_id}, {"$set": update_data})
    updated = await db.properties.find_one({"id": property_id}, {"_id": 0})
    if isinstance(updated.get('created_at'), str):
        updated['created_at'] = datetime.fromisoformat(updated['created_at'])
    return Property(**updated)

@api_router.delete("/properties/{property_id}")
async def delete_property(property_id: str):
    result = await db.properties.delete_one({"id": property_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Property not found")
    return {"message": "Property deleted successfully"}

# Enquiry  LeadRat CRM
@api_router.post("/enquiries", status_code=201)
async def create_enquiry(enquiry_data: EnquiryCreate):
    now = datetime.now(timezone.utc)
    enquiry_obj = Enquiry(**enquiry_data.model_dump())
    doc = enquiry_obj.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.enquiries.insert_one(doc)

    leadrat_synced = False
    if LEADRAT_API_KEY:
        try:
            leadrat_payload = {
                "name": enquiry_data.name,
                "mobile": enquiry_data.phone,
                "countryCode": "+91",
                "city": "Bangalore",
                "location": enquiry_data.location,
                "propertyType": enquiry_data.property_type,
                "budget": enquiry_data.budget,
                "notes": f"Enquiry Type: {enquiry_data.enquiry_type.upper()}. Budget/Price: {enquiry_data.budget}",
                "submittedDate": now.strftime("%d-%m-%Y"),
                "submittedTime": now.strftime("%H-%M-%S"),
                "additionalProperties": {
                    "EnquiredFor": "Buy" if enquiry_data.enquiry_type == "buy" else "Sale",
                    "Source": "Website - The NRI Realtor"
                }
            }
            resp = http_requests.post(LEADRAT_API_URL, headers={"API-Key": LEADRAT_API_KEY, "Content-Type": "application/json"}, json=leadrat_payload, timeout=15)
            if resp.status_code == 200:
                leadrat_synced = True
                await db.enquiries.update_one({"id": enquiry_obj.id}, {"$set": {"leadrat_synced": True}})
        except Exception as e:
            logging.error(f"LeadRat sync error: {e}")

    return {"success": True, "message": "Enquiry submitted successfully", "leadrat_synced": leadrat_synced}

@api_router.get("/enquiries")
async def get_enquiries():
    enquiries = await db.enquiries.find({}, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return enquiries

# Image Upload
@api_router.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    allowed = {
        "image/jpeg", "image/png", "image/webp", "image/gif",
        "application/pdf", "video/mp4", "video/webm", "video/quicktime"
    }

    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="File type not allowed")

    data = await file.read()

    if len(data) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size must be under 50MB")

    try:
        result = cloudinary.uploader.upload(
            data,
            folder="nri-realtor/properties",
            resource_type="auto"
        )

        return {
            "url": result.get("secure_url"),
            "path": result.get("public_id")
        }

    except Exception as e:
        logging.error(f"Cloudinary upload error: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")

@api_router.get("/files/{path:path}")
async def serve_file(path: str):
    record = await db.files.find_one({"storage_path": path, "is_deleted": False}, {"_id": 0})
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    data, content_type = get_object(path)
    return Response(content=data, media_type=record.get("content_type", content_type))

# Include router
app.include_router(api_router)

# CORS - allow all origins in production (configure as needed)
cors_origins = os.environ.get('CORS_ORIGINS', '*').split(',')
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"] if "*" in cors_origins else cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

@app.on_event("startup")
async def startup_event():
    try:
        if EMERGENT_KEY:
            init_storage()
            logging.info("Object storage initialized")
    except Exception as e:
        logging.warning(f"Storage init skipped: {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
git add .
git commit -m "add cloudinary upload"
git push
