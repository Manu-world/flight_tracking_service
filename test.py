import requests
from datetime import datetime
from typing import Dict, List, Optional, Union
from urllib.parse import urlencode

class FR24Tracker:
    """
    A client for the FlightRadar24 API to track flights and get airport information
    """
    
    def __init__(self, api_token: str, sandbox: bool = False):
        """
        Initialize the FR24 API client
        
        Args:
            api_token (str): Your FR24 API Bearer token
            sandbox (bool): Use sandbox environment for testing (default: False)
        """
        self.base_url = "https://fr24api.flightradar24.com/api"
        self.headers = {
            "Accept": "application/json",
            "Accept-Version": "v1",
            "Authorization": f"Bearer {api_token}"
        }
        if sandbox:
            self.base_url = f"{self.base_url}/sandbox"

    def get_live_flights(self, params: Dict[str, Union[str, int]], full_details: bool = True) -> Dict:
        """
        Get live flight positions with either full or light details
        
        Args:
            params: Dict containing query parameters (e.g., bounds, flights, airports)
            full_details: Whether to get full flight details (default: True)
            
        Returns:
            Dict containing flight data
        """
        endpoint = "/live/flight-positions/full" if full_details else "/live/flight-positions/light"
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            params=params
        )
        
        print("live flight: ", response.json())
        response.raise_for_status()
        return response.json()

    def track_flight_by_number(self, flight_number: str, full_details: bool = True) -> Dict:
        """
        Track a specific flight by its flight number (e.g., 'ETH516', 'UAE123')
        
        Args:
            flight_number: Flight number to track
            full_details: Whether to get full flight details (default: True)
            
        Returns:
            Dict containing flight data
            
        Example:
            tracker = FR24Tracker(api_token)
            flight = tracker.track_flight_by_number('ETH516')
            
            # Access flight details
            if flight['data']:
                position = flight['data'][0]
                print(f"Flight {position['flight']} is at:")
                print(f"Latitude: {position['lat']}")
                print(f"Longitude: {position['lon']}")
                print(f"Altitude: {position['alt']} feet")
                print(f"Ground Speed: {position['gspeed']} knots")
                
                if full_details:
                    print(f"Origin: {position['orig_iata']}")
                    print(f"Destination: {position['dest_iata']}")
                    print(f"ETA: {position['eta']}")
        """
        params = {
            "flights": flight_number,
            "limit": 1
        }
        return self.get_live_flights(params, full_details)

    def get_airport_details(self, code: str, full_details: bool = True) -> Dict:
        """
        Get airport information
        
        Args:
            code: Airport IATA or ICAO code
            full_details: Whether to get full airport details (default: True)
            
        Returns:
            Dict containing airport information
        """
        detail_type = "full" if full_details else "light"
        response = requests.get(
            f"{self.base_url}/static/airports/{code}/{detail_type}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

    def get_flight_tracks(self, flight_id: str) -> List[Dict]:
        """
        Get positional tracks for a specific flight
        
        Args:
            flight_id: FR24 flight ID in hexadecimal
            
        Returns:
            List containing flight track data
        """
        response = requests.get(
            f"{self.base_url}/flight-tracks",
            headers=self.headers,
            params={"flight_id": flight_id}
        )
        response.raise_for_status()
        return response.json()

    def track_flights_by_airport(self, airport_code: str, direction: str = "both") -> Dict:
        """
        Track flights for a specific airport
        
        Args:
            airport_code: Airport IATA or ICAO code
            direction: Flight direction ('both', 'inbound', or 'outbound')
            
        Returns:
            Dict containing flight data
        """
        params = {
            "airports": f"{direction}:{airport_code}",
            "limit": 100
        }
        return self.get_live_flights(params)

    def track_flights_by_bounds(self, north: float, south: float, 
                              west: float, east: float) -> Dict:
        """
        Track flights within geographical bounds
        
        Args:
            north: Northern latitude boundary
            south: Southern latitude boundary
            west: Western longitude boundary
            east: Eastern longitude boundary
            
        Returns:
            Dict containing flight data
        """
        params = {
            "bounds": f"{north},{south},{west},{east}",
            "limit": 100
        }
        return self.get_live_flights(params)

    def track_flights_by_airline(self, airline_code: str) -> Dict:
        """
        Track flights for a specific airline
        
        Args:
            airline_code: Airline ICAO code
            
        Returns:
            Dict containing flight data
        """
        params = {
            "operating_as": airline_code,
            "limit": 100
        }
        return self.get_live_flights(params)

    def calculate_eta(self, flight_data: Dict) -> Optional[str]:
        """
        Get the estimated time of arrival from flight data
        
        Args:
            flight_data: Flight data dictionary from API
            
        Returns:
            Formatted ETA string or None if not available
        """
        if "eta" in flight_data:
            eta_time = datetime.fromisoformat(flight_data["eta"].replace("Z", "+00:00"))
            return eta_time.strftime("%Y-%m-%d %H:%M:%S UTC")
        return None

    def get_historical_flights(self, timestamp: int, params: Dict[str, Union[str, int]], 
                             full_details: bool = True) -> Dict:
        """
        Get historical flight positions
        
        Args:
            timestamp: Unix timestamp for historical data
            params: Additional query parameters
            full_details: Whether to get full flight details (default: True)
            
        Returns:
            Dict containing historical flight data
        """
        params["timestamp"] = timestamp
        endpoint = "/historic/flight-positions/full" if full_details else "/historic/flight-positions/light"
        response = requests.get(
            f"{self.base_url}{endpoint}",
            headers=self.headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    
    
    
tracker = FR24Tracker(api_token="9dffe4b2-9bc6-4193-a55c-124de245ae08|GKdpULbmu72WayDv6OijEFqVvLfkkHvvbeCGWUgF41e5c027")

flight_data = tracker.track_flight_by_number('QR780')

print(flight_data)
# Print flight details
if flight_data['data']:
    flight = flight_data['data'][0]
    print(f"Flight: {flight['flight']}")
    print(f"Position: {flight['lat']}, {flight['lon']}")
    print(f"Altitude: {flight['alt']} feet")
    print(f"Ground Speed: {flight['gspeed']} knots")
    print(f"From: {flight['orig_iata']} To: {flight['dest_iata']}")
    print(f"ETA: {flight['eta']}")
else:
    print("Flight not found or not currently active")