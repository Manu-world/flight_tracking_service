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

    async def save_flight_search_history(self, user_id: str, flight_details: dict):
        db = await self._get_db()
        now = datetime.utcnow()
        
        # Fetch the existing document
        existing_doc = await db["flight_search_history"].find_one({"user_id": user_id})
        
        # Extract flight details
        flight_entry = {
            "number": flight_details["flight_number"],
            "date": now,
            "flight_iata": flight_details["flight_iata"],
            "departure": {
                "city": flight_details["dep_city"],
                "iata": flight_details["dep_iata"]
            },
            "arrival": {
                "city": flight_details["arr_city"],
                "iata": flight_details["arr_iata"]
            },
            "search_date": now
        }
        
        if existing_doc:
            existing_flights = existing_doc.get("flights", [])
            
            # Check if flight already exists and update it
            flight_updated = False
            for i, flight in enumerate(existing_flights):
                if flight["number"] == flight_entry["number"]:
                    existing_flights[i] = flight_entry
                    flight_updated = True
                    break
            
            if not flight_updated:
                existing_flights.append(flight_entry)
            
            # Update the document
            await db["flight_search_history"].update_one(
                {"user_id": user_id},
                {"$set": {"flights": existing_flights}},
                upsert=True
            )
        else:
            # Create new document
            await db["flight_search_history"].insert_one({
                "user_id": user_id,
                "flights": [flight_entry]
            })
        
        # Fetch and return the updated document
        updated_doc = await db["flight_search_history"].find_one({"user_id": user_id})
        return self._serialize_doc(updated_doc)
