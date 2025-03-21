import asyncio
import json
from datetime import datetime
import logging
from typing import Dict, Optional
from fastapi.encoders import jsonable_encoder
import httpx

from app.core.config import Settings, settings

logger = logging.getLogger(__name__)

class RapidFlightService:
    def __init__(self):
        self.API_URL = "https://flight-data4.p.rapidapi.com/get_flight_info"
        self.API_HEADERS = {
            "x-rapidapi-key": settings.RAPID_API_KEY,
            "x-rapidapi-host": "flight-data4.p.rapidapi.com"
        }
        self.UPDATE_INTERVAL = 60  # 60 seconds
        self._stop_event = asyncio.Event()
        
    async def fetch_flight_data(self, flight_icao: str, retries: int = 3) -> Optional[Dict]:
        """Fetch flight data with retry logic."""
        for attempt in range(retries):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        self.API_URL,
                        headers=self.API_HEADERS,
                        params={"flight": flight_icao}
                    )
                    await response.aread()  # Ensure response body is read
                    response.raise_for_status()
                    return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limit exceeded
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Rate limit exceeded. Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                    continue
                logger.error(f"HTTP error fetching flight data: {str(e)}")
                break
            except Exception as e:
                logger.error(f"Error fetching flight data: {str(e)}")
                break
        return None

    async def stop_streaming(self):
        """Stop the streaming loop."""
        self._stop_event.set()

    async def stream_flight_data(self, flight_icao: str):
        logger.info(f"Starting flight data stream for {flight_icao}")
        try:
            logger.debug(f"Fetching flight data for {flight_icao}")
            fetch_flight = await self.fetch_flight_data(flight_icao)
            flight_data = fetch_flight.get(flight_icao)
            
            if flight_data:
                logger.debug(f"Received flight data: {flight_data.get('flight')}")
                formatted_data = {
                    "flight_info": jsonable_encoder(flight_data.get("flight")),
                    "timestamp": datetime.utcnow().isoformat()
                }
                yield json.dumps(formatted_data)
            else:
                logger.warning("No flight data received")
                error_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": f"Flight {flight_icao} not found"
                }
                yield json.dumps(error_data)
                return  # Exit the generator when no flight is found
                
        except Exception as e:
            logger.error(f"Error in stream_flight_data: {str(e)}")
            error_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }
            yield json.dumps(error_data)
            return  # Exit the generator on error

        while not self._stop_event.is_set():
            try:
                await asyncio.sleep(self.UPDATE_INTERVAL)
                fetch_flight = await self.fetch_flight_data(flight_icao)
                flight_data = fetch_flight.get(flight_icao)
                
                if flight_data:
                    formatted_data = {
                        "flight_info": jsonable_encoder(flight_data.get("flight")),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    yield json.dumps(formatted_data)
                else:
                    break  # Exit the loop if flight data becomes unavailable
                    
            except Exception as e:
                logger.error(f"Error in stream_flight_data: {str(e)}")
                error_data = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "error": str(e)
                }
                yield json.dumps(error_data)
                break  # Exit the loop on error
                
        logger.info(f"Stopped flight data stream for {flight_icao}")

rapit_service = RapidFlightService()

# async def main():
#     flight_data = await rapit_service.fetch_flight_data("CA098")
#     print("flight data: ", flight_data)
    
#     return

# if __name__=="__main__":
#     asyncio.run(main())
    
    