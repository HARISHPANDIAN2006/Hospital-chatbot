import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:root@localhost:5432/hospital_db")

async def get_db_pool():
    """Create database connection pool"""
    return await asyncpg.create_pool(DATABASE_URL)

async def serialize_record(record):
    """Convert asyncpg record to dict"""
    if not record:
        return None
    return dict(record)