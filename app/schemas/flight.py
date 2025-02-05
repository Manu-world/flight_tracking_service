from pydantic import BaseModel, Field
from typing import Optional


class LiveDataSchema(BaseModel):
    updated_time: Optional[str] = Field(None, description="Last update time of the live flight data.")
    latitude: Optional[float] = Field(None, description="Latitude of the flight.")
    longitude: Optional[float] = Field(None, description="Longitude of the flight.")
    altitude: Optional[float] = Field(None, description="Altitude of the flight.")
    direction: Optional[float] = Field(None, description="Direction of the flight.")
    speed_horizontal: Optional[float] = Field(None, description="Horizontal speed of the flight.")
    speed_vertical: Optional[float] = Field(None, description="Vertical speed of the flight.")


class FlightDataResponseSchema(BaseModel):
    flight_number: Optional[str] = Field(None, description="Flight number.")
    airline: Optional[str] = Field(None, description="Airline name.")
    departure_airport: Optional[str] = Field(None, description="Departure airport.")
    arrival_airport: Optional[str] = Field(None, description="Arrival airport.")
    flight_status: Optional[str] = Field(None, description="Current flight status.")
    departure_time: Optional[str] = Field(None, description="Scheduled departure time.")
    arrival_time: Optional[str] = Field(None, description="Scheduled arrival time.")
    duration: Optional[str] = Field(None, description="Duration of the flight.")
    delay: Optional[int] = Field(None, description="Delay in minutes.")
    gate: Optional[str] = Field(None, description="Departure gate.")
    terminal: Optional[str] = Field(None, description="Departure terminal.")
    live: LiveDataSchema = Field(default_factory=LiveDataSchema, description="Live flight data.")
    description: Optional[str] = Field(None, description="Summary description of the flight details.")
