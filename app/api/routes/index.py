from fastapi import APIRouter

import logging
from app.api.routes import flight_updates_routes, websocket



logger = logging.getLogger(__name__)

router = APIRouter()



router.include_router(websocket.router)
router.include_router(flight_updates_routes.router)
