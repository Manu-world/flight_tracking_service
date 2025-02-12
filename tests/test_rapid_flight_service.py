# test_rapid_flight_service.py
import unittest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.rapid_flight_service import RapidFlightService

class TestRapidFlightService(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.service = RapidFlightService()
        
    @patch('httpx.AsyncClient.get')
    async def test_fetch_flight_data_success(self, mock_get):
        # Arrange
        flight_icao = "ABC123"
        expected_data = {"status": "success", "data": {"flight": flight_icao}}
        
        mock_response = MagicMock()
        mock_response.json = MagicMock(return_value=expected_data)
        mock_response.raise_for_status = AsyncMock()
        mock_response.aread = AsyncMock()
        mock_get.return_value = mock_response

        # Act
        result = await self.service.fetch_flight_data(flight_icao)

        # Assert
        self.assertEqual(result, expected_data)
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_awaited_once()
        mock_response.aread.assert_awaited_once()

    @patch('httpx.AsyncClient.get')
    async def test_fetch_flight_data_http_error(self, mock_get):
        # Arrange
        flight_icao = "ABC123"
        mock_response = MagicMock()
        mock_response.aread = AsyncMock()
        mock_response.raise_for_status = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                message="404 Not Found",
                request=MagicMock(),
                response=MagicMock(status_code=404)
            )
        )
        mock_get.return_value = mock_response

        # Act
        result = await self.service.fetch_flight_data(flight_icao)

        # Assert
        self.assertIsNone(result)
        mock_get.assert_called_once()
        mock_response.raise_for_status.assert_awaited_once()
        mock_response.aread.assert_awaited_once()

    @patch('httpx.AsyncClient.get')
    async def test_fetch_flight_data_network_error(self, mock_get):
        # Arrange
        flight_icao = "ABC123"
        mock_get.side_effect = httpx.RequestError("Network error")

        # Act
        result = await self.service.fetch_flight_data(flight_icao)

        # Assert
        self.assertIsNone(result)
        mock_get.assert_called_once()

    @patch('httpx.AsyncClient.get')
    @patch('asyncio.sleep')
    async def test_fetch_flight_data_rate_limit(self, mock_sleep, mock_get):
        # Arrange
        flight_icao = "ABC123"
        mock_response = MagicMock()
        mock_response.aread = AsyncMock()
        mock_response.raise_for_status = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                message="429 Too Many Requests",
                request=MagicMock(),
                response=MagicMock(status_code=429)
            )
        )
        mock_get.return_value = mock_response
        mock_sleep.return_value = None

        # Act
        result = await self.service.fetch_flight_data(flight_icao, retries=1)

        # Assert
        self.assertIsNone(result)
        self.assertEqual(mock_get.call_count, 2)  # Initial call + 1 retry
        mock_sleep.assert_awaited_once_with(1)  # 2^0 = 1 second wait on first retry

if __name__ == '__main__':
    unittest.main()