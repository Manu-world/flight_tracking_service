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
    
    
    
    