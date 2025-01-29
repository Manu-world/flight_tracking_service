from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum

class FlightCategory(str, Enum):
    PASSENGER = "P"
    CARGO = "C"
    MILITARY = "M"
    BUSINESS = "J"
    GENERAL = "T"
    HELICOPTER = "H"

class DataSource(str, Enum):
    ADSB = "ADSB"
    MLAT = "MLAT"
    ESTIMATED = "ESTIMATED"

class FlightPosition(BaseModel):
    lat: float = Field(..., description="Latitude")
    lon: float = Field(..., description="Longitude")
    altitude: int = Field(..., description="Altitude in feet")
    ground_speed: int = Field(..., description="Ground speed in knots")
    track: int = Field(..., description="Track angle in degrees")
    timestamp: datetime

class FlightRequest(BaseModel):
    bounds: Optional[str] = Field(None, description="Coordinates defining area (north,south,west,east)")
    flights: Optional[List[str]] = Field(None, description="List of flight numbers")
    categories: Optional[List[FlightCategory]] = None
    data_sources: Optional[List[DataSource]] = None
    limit: Optional[int] = Field(None, le=30000, description="Maximum number of results")

class FlightResponse(BaseModel):
    fr24_id: str
    flight_number: Optional[str]
    callsign: str
    position: FlightPosition
    aircraft_type: Optional[str]
    registration: Optional[str]
