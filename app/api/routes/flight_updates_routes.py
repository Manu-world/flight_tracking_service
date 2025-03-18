import json
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List, Optional
from pydantic import constr
from app.schemas.flight_updates_schema import FlightRequest, FlightResponse
from app.services.flight_updates_service import FlightUpdateService
from app.core.exceptions import ValidationError
from app.core.dependencies import get_current_user  
from app.db.database_service import DBService  
import logging
from app.services.rapid_flight_service import RapidFlightService  
from fastapi import status
from fastapi.responses import JSONResponse, StreamingResponse


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["Flight"])

# Rate limiting constants
RATE_LIMIT = 10  
RATE_LIMIT_WINDOW = 60  


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


@router.get("/flights/info/{flight_number}", response_model=FlightResponse)
async def get_flight_info(
    flight_number: str,  
    current_user: dict = Depends(get_current_user)
) -> JSONResponse:
    """
    Get flight information by flight number.
    Requires authentication.
    """
    try:
        logger.info(f"Fetching flight info for flight number: {flight_number} by user: {current_user['id']}")

        if not flight_number.isalnum():
            raise ValidationError(detail="Invalid flight number format. Must be alphanumeric.")

        # Initialize services
        rapid_service = RapidFlightService()
        db_service = DBService()

        
        flight_data = await rapid_service.fetch_flight_data(flight_number)
        
        # Check if flight data is valid
        if not flight_data or not flight_data.get(flight_number):
            logger.warning(f"Flight not found: {flight_number}")
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "status": False,
                    "data": None,
                    "message": "Flight not found."
                }
            )

        
        flight_info = flight_data.get(flight_number)
        
        # Prepare flight details for history
        flight_details = {
            "flight_number": flight_number,
            "flight_iata": flight_info.get("flight", {}).get("iata"),
            "dep_city": flight_info.get("dep_airport", {}).get("city"),
            "dep_iata": flight_info.get("dep_airport", {}).get("iata"),
            "arr_city": flight_info.get("arr_airport", {}).get("city"),
            "arr_iata": flight_info.get("arr_airport", {}).get("iata")
        }
        
        # Save to search history with additional details
        await db_service.save_flight_search_history(
            user_id=str(current_user["id"]),
            flight_details=flight_details
        )

        
        logger.info(f"Successfully fetched flight info for: {flight_number}")
        
        
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
