from fastapi import logger
from motor.motor_asyncio import AsyncIOMotorClient
# from pymongo import IndexModel, ASCENDING
from datetime import datetime
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)

class Database:
    client: AsyncIOMotorClient = None
    
    @classmethod
    async def connect_db(cls):
        try:
            cls.client = AsyncIOMotorClient(settings.MONGODB_URL)
            
            await cls.client.admin.command("ping")
            
            
            # Create indexes
            db = cls.client.flight_tracker
            
            # await db.users.create_indexes([
            #     IndexModel([("email", ASCENDING)], unique=True),
            #     IndexModel([("auth_provider", ASCENDING)]),
            # ])
            
            

            # Get the list of available collections in the database
        
            collection_names = await db.list_collection_names()
            logging.info("Connected to the database.")
            logging.info("Available collections:")
            for collection_name in collection_names:
                logging.info(collection_name)

            return True
        except Exception as e:
            logging.error(f"MongoDB connection failed: {e}")
            raise
    
    @classmethod
    async def close_db(cls):
        if cls.client is not None:
            await cls.client.close()
        else:
            logging.warning("Attempted to close a database connection, but no client was initialized.")
    
    @classmethod
    async def get_db(cls):
        if cls.client is None:
            await cls.connect_db()
        return cls.client.flight_tracker
