from typing import Optional, Dict
import httpx
from fastapi import HTTPException, status
from app.schemas.flight import FlightDataResponseSchema, LiveDataSchema
from app.core.config import Settings
from app.core.logging import logger
from datetime import datetime
import re
import asyncio
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

class FlightService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.client = httpx.AsyncClient(
            timeout=settings.API_TIMEOUT,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    @staticmethod
    def validate_flight_icao(flight_icao: str) -> bool:
        """Validate ICAO flight identifier format."""
        return bool(re.match(r'^[A-Z0-9]{6,8}$', flight_icao.upper()))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )
    async def fetch_flight_data(self, flight_iata: str) -> Optional[Dict]:
        """
        Fetch flight data from the aviation API with retry logic and circuit breaking.
        """
        try:
            logger.info(f"Fetching flight data for {flight_iata}")
            response = await self.client.get(
                self.settings.AVIATION_API_URL,
                params={
                    "access_key": self.settings.AVIATION_STACK_API_KEY,
                    "flight_iata": flight_iata
                }
            )
                    # "flight_icao": flight_icao,
            response.raise_for_status()
            data = response.json()
            print("data: ",data)
            
            logger.info(f"Received data from aviationstack: {data}")
            
            if not data or "data" not in data:
                logger.warning(f"No data received for flight {flight_iata}")
                return None

            flights = data.get("data", [])
            if not flights:
                logger.warning(f"No flights found for {flight_iata}")
                return None
            
            return flights[0]

        except httpx.HTTPStatusError as e:
            logger.error(f"API request failed with status {e.response.status_code}")
            if e.response.status_code == 429:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded"
                )
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="External service unavailable"
            )
        except Exception as e:
            logger.exception("Unexpected error in fetch_flight_data")
            raise

    async def format_flight_data(self, raw_data: Dict) -> FlightDataResponseSchema:
        """Format raw flight data into the response schema with additional validation."""
        try:
            flight_info = raw_data
            departure_time = self._parse_datetime(flight_info.get("departure", {}).get("scheduled"))
            arrival_time = self._parse_datetime(flight_info.get("arrival", {}).get("scheduled"))
            
            duration = None
            if departure_time and arrival_time:
                duration = str(arrival_time - departure_time)

            live_data = flight_info.get("live", {})
            live = LiveDataSchema(
                updated_time=self._parse_datetime(live_data.get("updated")).isoformat() if self._parse_datetime(live_data.get("updated")) else None,
                latitude=self._validate_coordinate(live_data.get("latitude")),
                longitude=self._validate_coordinate(live_data.get("longitude")),
                altitude=self._validate_numeric(live_data.get("altitude")),
                direction=self._validate_direction(live_data.get("direction")),
                speed_horizontal=self._validate_numeric(live_data.get("speed_horizontal")),
                speed_vertical=self._validate_numeric(live_data.get("speed_vertical")),
            )

            return FlightDataResponseSchema(
                flight_number=flight_info.get("flight", {}).get("number"),
                airline=flight_info.get("airline", {}).get("name"),
                departure_airport=flight_info.get("departure", {}).get("airport"),
                arrival_airport=flight_info.get("arrival", {}).get("airport"),
                flight_status=self._normalize_status(flight_info.get("flight_status")),
                departure_time=departure_time.isoformat() if departure_time else None,
                arrival_time=arrival_time.isoformat() if arrival_time else None,
                duration=duration,
                delay=self._validate_numeric(flight_info.get("departure", {}).get("delay")),
                gate=flight_info.get("departure", {}).get("gate"),
                terminal=flight_info.get("departure", {}).get("terminal"),
                live=live,
                description=self._generate_description(flight_info)
            )
        except Exception as e:
            logger.exception("Error formatting flight data")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error processing flight data"
            )

    @staticmethod
    def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
        """Parse datetime string with error handling."""
        if not dt_str:
            return None
        try:
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _validate_coordinate(value: Optional[float]) -> Optional[float]:
        """Validate geographic coordinates."""
        if value is None:
            return None
        try:
            value = float(value)
            if -180 <= value <= 180:
                return value
            return None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _validate_direction(value: Optional[float]) -> Optional[float]:
        """Validate direction in degrees."""
        if value is None:
            return None
        try:
            value = float(value)
            if 0 <= value < 360:
                return value
            return None
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _validate_numeric(value: Optional[float]) -> Optional[float]:
        """Validate numeric values."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _normalize_status(status: Optional[str]) -> Optional[str]:
        """Normalize flight status values."""
        if not status:
            return None
        status_map = {
            'scheduled': 'SCHEDULED',
            'active': 'ACTIVE',
            'landed': 'LANDED',
            'cancelled': 'CANCELLED',
            'diverted': 'DIVERTED',
            'incident': 'INCIDENT',
            'unknown': 'UNKNOWN'
        }
        return status_map.get(status.lower(), 'UNKNOWN')

    def _generate_description(self, flight_info: Dict) -> str:
        """Generate a human-readable flight description."""
        parts = []
        
        # Add flight identification
        if flight_num := flight_info.get("flight", {}).get("number"):
            if airline := flight_info.get("airline", {}).get("name"):
                parts.append(f"{airline} flight {flight_num}")
            else:
                parts.append(f"Flight {flight_num}")

        # Add route information
        dep = flight_info.get("departure", {}).get("airport")
        arr = flight_info.get("arrival", {}).get("airport")
        if dep and arr:
            parts.append(f"from {dep} to {arr}")

        # Add status and timing
        if status := self._normalize_status(flight_info.get("flight_status")):
            parts.append(f"is {status.lower()}")

        if delay := flight_info.get("departure", {}).get("delay"):
            parts.append(f"with a {delay} minute delay")

        # Add gate/terminal info if available
        gate = flight_info.get("departure", {}).get("gate")
        terminal = flight_info.get("departure", {}).get("terminal")
        if gate and terminal:
            parts.append(f"at gate {gate}, terminal {terminal}")
        elif gate:
            parts.append(f"at gate {gate}")
        elif terminal:
            parts.append(f"at terminal {terminal}")

        return " ".join(parts)

# async def main():
#     settings = Settings()  # You'll need to ensure your Settings class can be instantiated without arguments
#     async with FlightService(settings) as service:
#         flight_data = await service.fetch_flight_data("CA908")
#         print("Flight Data:", flight_data)

# if __name__ == "__main__":
#     asyncio.run(main())