import asyncio
import json
from datetime import datetime
from typing import Dict, Optional
import logging
from fastapi.encoders import jsonable_encoder
from app.core.config import settings
from app.services.flight_updates_service import FlightUpdateService
from app.services.flight_service import FlightService
from app.schemas.flight_updates_schema import FlightRequest

logger = logging.getLogger(__name__)

class CombinedFlightService:
    def __init__(self):
        self.position_service = FlightUpdateService()
        self.flight_service = FlightService(settings)
        self.POSITION_UPDATE_INTERVAL = 60  # 30 seconds
        self.FLIGHT_INFO_UPDATE_INTERVAL = 120  # 2 minutes

    async def fetch_position_data(self, flight_icao: str) -> Optional[Dict]:
        """Fetch position data for a flight"""
        try:
            position_data = await self.position_service.get_live_flights(
                FlightRequest(flights=[flight_icao])
            )
            # Position data is now a list of FlightResponse objects
            if position_data and len(position_data) > 0:
                flight = position_data[0]  # Get first flight
                return {
                    'lat': flight.position.lat,
                    'lon': flight.position.lon,
                    'alt': flight.position.altitude,
                    'track': flight.position.track,
                    'ground_speed': flight.position.ground_speed,
                    'timestamp': flight.position.timestamp
                }
            return None
        except Exception as e:
            logger.error(f"Error fetching position data: {str(e)}")
            return None

    async def fetch_flight_info(self, flight_icao: str) -> Optional[Dict]:
        """Fetch flight information"""
        try:
            raw_data = await self.flight_service.fetch_flight_data(flight_icao)
            if raw_data:
                # Format the data using the existing service method
                formatted_data = await self.flight_service.format_flight_data(raw_data)
                return formatted_data
            return None
        except Exception as e:
            logger.error(f"Error fetching flight info: {str(e)}")
            return None

    async def stream_combined_flight_data(self, flight_icao: str):
        """
        Stream combined flight data with:
        - Position updates every 30 seconds
        - Flight info updates every 2 minutes
        """
        flight_info = None
        last_flight_info_update = 0
        last_position_update = 0

        while True:
            try:
                current_time = asyncio.get_event_loop().time()
                update_position = (current_time - last_position_update) >= self.POSITION_UPDATE_INTERVAL
                update_flight_info = (current_time - last_flight_info_update) >= self.FLIGHT_INFO_UPDATE_INTERVAL
                # Update flight info if needed
                if update_flight_info:
                    new_flight_info = await self.fetch_flight_info(flight_icao)
                    if new_flight_info:  
                        flight_info_with_airport_details = await self.position_service.update_airport_details(new_flight_info)
                        flight_info= flight_info_with_airport_details if flight_info_with_airport_details else flight_info
                        
                        
                        
                    last_flight_info_update = current_time

                # Update position if needed
                position_data = None
                if update_position:
                    position_data = await self.fetch_position_data(flight_icao)
                    last_position_update = current_time


                # Combine and send data if either was updated
                if update_position or update_flight_info:
                    combined_data = {
                        "flight_info": jsonable_encoder(flight_info) if flight_info else None,
                        "live": jsonable_encoder(position_data),
                        "timestamp": datetime.utcnow().isoformat(),
                        "update_type": {
                            "position": update_position,
                            "flight_info": update_flight_info
                        }
                    }
                    
                    yield json.dumps(combined_data)

                # Calculate sleep time until next update
                time_to_next_position = self.POSITION_UPDATE_INTERVAL - (current_time - last_position_update)
                time_to_next_flight_info = self.FLIGHT_INFO_UPDATE_INTERVAL - (current_time - last_flight_info_update)
                sleep_time = min(time_to_next_position, time_to_next_flight_info)
                
                await asyncio.sleep(max(1, sleep_time))  # Ensure minimum 1 second sleep

            except Exception as e:
                logger.error(f"Error in stream_combined_flight_data: {str(e)}")
                error_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e)
                }
                yield json.dumps(error_data)
                await asyncio.sleep(5)  # Wait before retry
                
                
combine_flight=CombinedFlightService()

# import asyncio

# if __name__ == "__main__":
#     async def main():
#         async for data in combine_flight.stream_combined_flight_data("CA908"):
#             print(data)  # Process the yielded data as needed

#     asyncio.run(main())               