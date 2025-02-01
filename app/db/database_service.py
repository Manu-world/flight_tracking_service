# services/user_service.py
from datetime import datetime
from bson import ObjectId
from fastapi import HTTPException, status

# from app.models.user import UserInDB, UserUpdate
from app.db.config import Database

class DBService:
    def __init__(self):
        self.db = None
    
    async def _get_db(self):
        if self.db is None:
            self.db = await Database.get_db()
        return self.db

    
    async def get_latest_item(self, collection_name: str, search_field: str, search_value):
        db = await self._get_db()
        query = {search_field: search_value}
        latest_item = await db[collection_name].find_one(query, sort=[("created_at", -1)])
        if latest_item is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No items found")
        return latest_item
    
    def _serialize_doc(self, doc):
        """Helper method to serialize MongoDB document"""
        if doc.get('_id'):
            doc['_id'] = str(doc['_id'])
        return doc

    async def get_user_flight_search_history(self, user_id: str, limit: int = 10):
        db = await self._get_db()
        # Now we'll just find one document per user
        doc = await db["flight_search_history"].find_one({"user_id": user_id})
        if doc:
            return self._serialize_doc(doc)
        return None

    async def save_flight_search_history(self, user_id: str, flights: list[str]):
        db = await self._get_db()
        now = datetime.utcnow()
        
        # Format new flight entries
        new_flights = [{"number": flight, "date": now} for flight in flights]
        
        # Try to update existing document
        result = await db["flight_search_history"].update_one(
            {"user_id": user_id},
            {
                "$push": {
                    "flights": {
                        "$each": new_flights,
                    }
                }
            },
            upsert=True  # Create if doesn't exist
        )
        
        # Fetch and return the updated document
        updated_doc = await db["flight_search_history"].find_one({"user_id": user_id})
        return self._serialize_doc(updated_doc)
    
    
    
    