from pydantic import BaseModel, Field
from typing import Any, Optional, Dict

class AirportDetailsSchema(BaseModel):
    name: str = Field(None, description="Airport name")
    iata: str = Field(None, description="IATA code")
    icao: str = Field(None, description="ICAO code")
    lon: float = Field(None, description="Longitude")
    lat: float = Field(None, description="Latitude")
    elevation: int = Field(None, description="Elevation in feet")
    country: Dict[str, str] = Field(None, description="Country information")
    city: str = Field(None, description="City name")
    state: Optional[str] = Field(None, description="State name")
    timezone: Dict[str, Any] = Field(None, description="Timezone information")

class FlightDataResponseSchema(BaseModel):
    flight_number: Optional[str] = Field(None, description="Flight number")
    airline: Optional[str] = Field(None, description="Airline name")
    departure_airport: Optional[str] = Field(None, description="Departure airport code")
    departure_airport_details: Optional[AirportDetailsSchema] = Field(None, description="Detailed departure airport information")
    arrival_airport: Optional[str] = Field(None, description="Arrival airport code")
    arrival_airport_details: Optional[AirportDetailsSchema] = Field(None, description="Detailed arrival airport information")
    flight_status: Optional[str] = Field(None, description="Current flight status")
    departure_time: Optional[str] = Field(None, description="Scheduled departure time")
    arrival_time: Optional[str] = Field(None, description="Scheduled arrival time")
    duration: Optional[str] = Field(None, description="Duration of the flight")
    delay: Optional[int] = Field(None, description="Delay in minutes")
    gate: Optional[str] = Field(None, description="Departure gate")
    terminal: Optional[str] = Field(None, description="Departure terminal")
    description: Optional[str] = Field(None, description="Summary description of the flight details")


class AirportDetails(BaseModel):
    name: str
    iata: str
    icao: str
    lon: float
    lat: float
    elevation: int
    country: Dict[str, str]
    city: str
    state: Optional[str]
    timezone: Dict[str, Any]
