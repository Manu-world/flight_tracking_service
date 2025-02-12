import json
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from pydantic import constr
from app.schemas.flight_updates_schema import FlightRequest, FlightResponse
from app.services.flight_updates_service import FlightUpdateService
from app.core.exceptions import ValidationError
from app.core.dependencies import get_current_user  # Import the auth dependency
from app.db.database_service import DBService  # Add this import
import logging
from app.services.rapid_flight_service import RapidFlightService  # Add this import
from fastapi import status
from fastapi.responses import JSONResponse, StreamingResponse

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Flight"])

# Rate limiting constants
RATE_LIMIT = 10  # Max requests per minute
RATE_LIMIT_WINDOW = 60  # Time window in seconds

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

@router.get("/flights/info/{flight_number}", response_model=FlightResponse)
async def get_flight_info(
    flight_number: str,  # Validate flight number length
    current_user: dict = Depends(get_current_user)
) -> JSONResponse:
    """
    Get flight information by flight number.
    Requires authentication.
    """
    try:
        # Log the request
        logger.info(f"Fetching flight info for flight number: {flight_number} by user: {current_user['id']}")

        # Validate flight number format (e.g., alphanumeric)
        if not flight_number.isalnum():
            raise ValidationError(detail="Invalid flight number format. Must be alphanumeric.")

        # Initialize services
        rapid_service = RapidFlightService()
        db_service = DBService()

        # Fetch flight data
        flight_data = await rapid_service.fetch_flight_data(flight_number)
        
        # Check if flight data is valid
        if not flight_data or not flight_data.get(flight_number):
            logger.warning(f"Flight not found: {flight_number}")
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "status": False,
                    "data": None,
                    "message": "Flight not found."
                }
            )

        # Save flight info request to user's search history
        await db_service.save_flight_search_history(
            user_id=str(current_user["id"]),
            flights=[flight_number]
        )

        # Log successful response
        logger.info(f"Successfully fetched flight info for: {flight_number}")
        
        # Extract flight data for the specific flight number
        flight_info = flight_data.get(flight_number)

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": True,
                "data": flight_info,
                "message": "Flight information retrieved successfully."
            }
        )

    except ValidationError as ve:
        logger.error(f"Validation error: {ve.detail}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "status": False,
                "data": None,
                "message": ve.detail
            }
        )

    except HTTPException as he:
        # Re-raise HTTPException to maintain FastAPI's error handling
        raise he

    except Exception as e:
        logger.error(f"Unexpected error fetching flight info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "status": False,
                "data": None,
                "message": "An unexpected error occurred while fetching flight information."
            }
        )
