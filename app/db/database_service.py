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
        doc = await db["flight_search_history"].find_one({"user_id": user_id}, sort=[("flights.date", -1)])
        if doc:
            return self._serialize_doc(doc)
        return None

    async def save_flight_search_history(self, user_id: str, flights: list[str]):
        db = await self._get_db()
        now = datetime.utcnow()
        
        # Fetch the existing document
        existing_doc = await db["flight_search_history"].find_one({"user_id": user_id})
        
        if existing_doc:
            # If the document exists, check for duplicates
            existing_flights = existing_doc.get("flights", [])
            updated_flights = []
            
            # Create a set of existing flight numbers for quick lookup
            existing_flight_numbers = {flight["number"] for flight in existing_flights}
            
            for flight in flights:
                if flight in existing_flight_numbers:
                    # If the flight already exists, update its date
                    for existing_flight in existing_flights:
                        if existing_flight["number"] == flight:
                            existing_flight["date"] = now
                            break
                else:
                    # If the flight doesn't exist, add it
                    updated_flights.append({"number": flight, "date": now})
            
            # Combine the updated existing flights with the new flights
            updated_flights = existing_flights + updated_flights
            
            # Update the document with the new flights array
            result = await db["flight_search_history"].update_one(
                {"user_id": user_id},
                {"$set": {"flights": updated_flights}},
                upsert=True  # Create if doesn't exist
            )
        else:
            # If the document doesn't exist, create a new one with the flights
            new_flights = [{"number": flight, "date": now} for flight in flights]
            result = await db["flight_search_history"].insert_one(
                {"user_id": user_id, "flights": new_flights}
            )
        
        # Fetch and return the updated document
        updated_doc = await db["flight_search_history"].find_one({"user_id": user_id})
        return self._serialize_doc(updated_doc)
