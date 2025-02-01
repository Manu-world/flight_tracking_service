from fastapi import APIRouter, Depends, Query
from typing import List
from app.schemas.flight_updates_schema import FlightRequest, FlightResponse
from app.services.flight_updates_service import FlightUpdateService
from app.core.exceptions import ValidationError
from fastapi.responses import StreamingResponse
import asyncio
from app.core.dependencies import get_current_user  # Import the auth dependency
from app.db.database_service import DBService  # Add this import

router = APIRouter(tags=["Flight"])

@router.get("/flights/live", response_model=List[FlightResponse])
async def get_live_flights(
    current_user: dict = Depends(get_current_user),  # Add auth dependency
    bounds: str = Query(None, description="Coordinates defining area (north,south,west,east)"),
    flights: List[str] = Query(None, description="List of flight numbers"),
    limit: int = Query(None, le=30000, description="Maximum number of results")
) -> List[FlightResponse]:
    """
    Get live flight positions with optional filtering.
    Requires authentication.
    """
    request = FlightRequest(
        bounds=bounds,
        flights=flights,
        limit=limit
    )
    
    # Save search history
    db_service = DBService()
    await db_service.save_flight_search_history(
        user_id=str(current_user["id"]),
        flights=flights
    )
    
    print("user: ", current_user)
    
    service = FlightUpdateService()
    return await service.get_live_flights(request)

@router.get("/flights/live/stream")
async def stream_live_flights(
    current_user: dict = Depends(get_current_user),  # Add auth dependency
    bounds: str = Query(None, description="Coordinates defining area (north,south,west,east)"),
    flights: List[str] = Query(None, description="List of flight numbers"),
    limit: int = Query(None, le=30000, description="Maximum number of results")
) -> StreamingResponse:
    """
    Stream live flight positions with updates every 30 seconds using Server-Sent Events.
    Requires authentication.
    """
    request = FlightRequest(
        bounds=bounds,
        flights=flights,
        limit=limit
    )
    
    print("user: ", current_user)
    
    service = FlightUpdateService()
    
    return StreamingResponse(
        service.stream_live_flights(request),
        media_type="text/event-stream",
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disable buffering in nginx
        }
    )

@router.get("/flights/search-history")
async def get_flight_search_history(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(10, le=100, description="Maximum number of history items to return")
):
    """
    Retrieve user's flight search history.
    Requires authentication.
    """
    db_service = DBService()
    history = await db_service.get_user_flight_search_history(
        user_id=str(current_user["id"]),
        limit=limit
    )
    return history