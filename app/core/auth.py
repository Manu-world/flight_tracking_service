from fastapi import HTTPException, Security, Depends, WebSocket
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import httpx
from typing import Optional
import json
import logging
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

class AuthMiddleware:
    def __init__(self):
        self.security = HTTPBearer()
        self.verify_url = "https://fastapi-auth-4rl3.onrender.com/api/v1/auth/verify"
        self.timeout = httpx.Timeout(10.0, connect=5.0)  # 10s timeout, 5s connect timeout
        
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type(httpx.RequestError)
    )
    async def _make_auth_request(self, token: str) -> dict:
        """Make HTTP request to auth service with retry logic"""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(
                    self.verify_url,
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid or expired token"
                    )
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Auth service error: {e.response.text}"
                )
            except httpx.RequestError as e:
                logger.error(f"Request to auth service failed: {str(e)}")
                raise
    async def verify_token(self, credentials: HTTPAuthorizationCredentials = Security(HTTPBearer())) -> dict:
        """
        Verify JWT token with external auth service and return user details
        """
        token = credentials.credentials
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    self.verify_url,
                    headers={"Authorization": f"Bearer {token}"}
                )
                
                if response.status_code == 401:
                    raise HTTPException(
                        status_code=401,
                        detail="Invalid or expired token"
                    )
                elif response.status_code != 200:
                    raise HTTPException(
                        status_code=500,
                        detail="Error verifying token"
                    )
                
                # Extract user details from the response
                user_data = response.json().get("data")
                if not user_data:
                    raise HTTPException(
                        status_code=500,
                        detail="No user data found in response"
                    )
                return user_data 
            except httpx.RequestError:
                raise HTTPException(
                    status_code=503,
                    detail="Authentication service unavailable"
                )
                
    async def decode_token(self, token: str) -> dict:
        """
        Verify JWT token with external auth service and return user details
        """
        try:
            response_data = await self._make_auth_request(token)
            
            user_data = response_data.get("data")
            if not user_data:
                raise HTTPException(
                    status_code=500,
                    detail="No user data found in response"
                )
            return user_data
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token verification failed: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail="Authentication service unavailable"
            )


# WebSocket authentication functions
async def get_token_from_query(websocket: WebSocket) -> str:
    """Extract token from WebSocket query parameters"""
    try:
        token = websocket.query_params.get("token")
        if not token:
            raise HTTPException(status_code=403, detail="Missing authentication token")
        logger.debug(f"Extracted token: {token[:20]}...")
        return token
    except Exception as e:
        logger.error(f"Error extracting token: {str(e)}")
        raise HTTPException(status_code=403, detail="Error extracting authentication token")

async def authenticate_websocket(websocket: WebSocket) -> dict:
    """Authenticate WebSocket connection with retry logic"""
    try:
        token = await get_token_from_query(websocket)
        auth_handler = AuthMiddleware()
        
        # Try authentication with retries
        for attempt in range(3):
            try:
                user = await auth_handler.decode_token(token)
                logger.debug(f"Authentication successful for user: {user.get('id', 'unknown')}")
                return user
            except HTTPException as e:
                if e.status_code != 503 or attempt == 2:  # Don't retry on non-503 errors or last attempt
                    raise
                await asyncio.sleep(1 * (attempt + 1))  
                
    except HTTPException as e:
        logger.error(f"Authentication failed: {e.detail}")
        raise
    except Exception as e:
        logger.error(f"Unexpected authentication error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal authentication error")
    