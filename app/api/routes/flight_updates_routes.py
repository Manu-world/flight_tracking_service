import json
from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect,HTTPException
from typing import List
from app.schemas.flight_updates_schema import FlightRequest, FlightResponse
from app.services.flight_updates_service import FlightUpdateService
from app.core.exceptions import ValidationError
from fastapi.responses import StreamingResponse
from app.core.dependencies import get_current_user  # Import the auth dependency
from app.db.database_service import DBService  # Add this import
import logging
from app.core.auth import AuthMiddleware, authenticate_websocket
import asyncio
from app.services.combined_flight_update import CombinedFlightService

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
            'X-Accel-Buffering': 'no' 
        }
    )

@router.websocket("/ws/flight/{flight_icao}")
async def websocket_flight_data(websocket: WebSocket, flight_icao: str):
    """WebSocket endpoint for streaming flight data"""
    connection_active = False
    
    try:
        logger.debug(f"New WebSocket connection attempt for flight {flight_icao}")
        
        # Accept the connection first so we can send error messages if needed
        await websocket.accept()
        connection_active = True
        
        # Authenticate after accepting connection
        user = await authenticate_websocket(websocket)
        logger.info(f"User {user['id']} connected to flight {flight_icao}")
        
        combined_service = CombinedFlightService()
        
        async for data in combined_service.stream_combined_flight_data(flight_icao):
            try:
                await websocket.send_text(data)
            except WebSocketDisconnect:
                logger.info("Client disconnected during streaming")
                break
            except Exception as e:
                logger.error(f"Error sending data: {str(e)}")
                break
                
    except WebSocketDisconnect:
        logger.info("Client disconnected normally")
    
    except HTTPException as e:
        logger.error(f"HTTP Exception during WebSocket handling: {e.detail}")
        if not connection_active:
            await websocket.accept()
        try:
            await websocket.send_text(json.dumps({"error": str(e.detail)}))
            await websocket.close(code=1008, reason=str(e.detail))
        except Exception as close_error:
            logger.error(f"Error during connection closure: {str(close_error)}")
    
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket handler: {str(e)}", exc_info=True)
        if not connection_active:
            await websocket.accept()
        try:
            await websocket.send_text(json.dumps({"error": "Internal server error"}))
            await websocket.close(code=1011)
        except Exception as close_error:
            logger.error(f"Error during error handling: {str(close_error)}")
    
    finally:
        # Ensure we close the connection if it's still open
        if connection_active:
            try:
                await websocket.close()
            except Exception as e:
                logger.error(f"Error closing websocket: {str(e)}")