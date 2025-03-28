from typing import Dict, List, Optional
import httpx
from app.core.config import settings
from app.core.exceptions import FlightRadarAPIException
import logging
from app.schemas.flight import AirportDetails
from app.schemas.flight_updates_schema import FlightPosition, FlightRequest, FlightResponse
import asyncio
import json
from fastapi.encoders import jsonable_encoder
from datetime import datetime

class FlightUpdateService:
    def __init__(self):
        self.settings = settings
        self.logger = logging.getLogger("flight_radar_api")
        self.base_url = self.settings.FR24_BASE_URL
        self.headers = {
            "Accept": "application/json",
            "Accept-Version": self.settings.FR24_API_VERSION,
            "Authorization": "Bearer 0dbec09dad9576f7e7119ac44b49ea91"
            # TODO: change to env variable
        }

    async def get_live_flights(self, request: FlightRequest) -> List[FlightResponse]:
        """
        Get live flight positions with filtering options.
        """
        try:
            print("get_live_flights hit")
            params = self._build_query_params(request)
            print("params",params)
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}live/flight-positions/full",
                    headers=self.headers,
                    params=params,
                    timeout=30.0
                )
                response.raise_for_status()
                print("full live updates: ", response.json())
                
                
                return self._process_flight_data(response.json())
                
        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error occurred: {str(e)}")
            raise FlightRadarAPIException(f"Failed to fetch flight data: {str(e)}")
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise FlightRadarAPIException(f"Unexpected error occurred: {str(e)}")
        
    async def stream_live_flights(self, request: FlightRequest):
        """
        Stream live flight positions with updates every 30 seconds.
        Yields JSON-encoded flight data.
        """
        while True:
            try:
                flights = await self.get_live_flights(request)
                
                # Convert to dict and add timestamp
                data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "flights": jsonable_encoder(flights)
                }
                yield f"data: {json.dumps(data)}\n\n"
                
                await asyncio.sleep(30)  # Wait for 30 seconds before next update
                
            except Exception as e:
                self.logger.error(f"Error in flight stream: {str(e)}")
                # Send error message to client
                error_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e)
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                await asyncio.sleep(5)  # Wait a bit before retrying

    def _build_query_params(self, request: FlightRequest) -> Dict:
        """
        Build query parameters from request model.
        """
        params = {}
        
        if request.bounds:
            params["bounds"] = request.bounds
        if request.flights:
            params["flights"] = ",".join(request.flights)
        if request.categories:
            params["categories"] = ",".join([cat.value for cat in request.categories])
        if request.data_sources:
            params["data_sources"] = ",".join([src.value for src in request.data_sources])
        if request.limit:
            params["limit"] = request.limit
            
        return params

    def _process_flight_data(self, raw_data: Dict) -> List[FlightResponse]:
        """
        Process and validate raw flight data into response models.
        """
        # Handle case where raw_data is an empty list
        if isinstance(raw_data, list):
            return []
        
        flights = []
        for item in raw_data.get("data", []):
            try:
                flight = FlightResponse(
                    fr24_id=item["fr24_id"],
                    flight_number=item.get("flight"),
                    callsign=item["callsign"],
                    position=FlightPosition(
                        lat=item["lat"],
                        lon=item["lon"],
                        altitude=item["alt"],
                        ground_speed=item["gspeed"],
                        track=item["track"],
                        timestamp=item["timestamp"]
                    ),
                    aircraft_type=item.get("type"),
                    registration=item.get("reg")
                )
                flights.append(flight)
            except KeyError as e:
                self.logger.warning(f"Missing required field in flight data: {e}")
                continue
                
        return flights
    
    async def get_airport_details(self, airport_code: str) -> Optional[AirportDetails]:
        """
        Fetch detailed airport information by IATA/ICAO code.
        
        Args:
            airport_code (str): IATA or ICAO airport code
            
        Returns:
            Optional[AirportDetails]: Airport details if found, None otherwise
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}static/airports/{airport_code}/full",
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                
                data = response.json()
                return AirportDetails(**data)
                
        except httpx.HTTPError as e:
            self.logger.error(f"HTTP error occurred while fetching airport details: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error while fetching airport details: {str(e)}")
            return None
    
    async def update_airport_details(self, flight: FlightResponse) -> FlightResponse:
        """
        Enrich flight data with departure and arrival airport details.
        """
        if hasattr(flight, 'departure_airport'):
            dep_details = await self.get_airport_details(flight.departure_airport)
            if dep_details:
                flight.departure_airport_details = dep_details

        if hasattr(flight, 'arrival_airport'):
            arr_details = await self.get_airport_details(flight.arrival_airport)
            if arr_details:
                flight.arrival_airport_details = arr_details

        return flight


flight_service = FlightUpdateService()

