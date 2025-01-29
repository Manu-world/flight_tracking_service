from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import httpx
from typing import Optional
import json

class AuthMiddleware:
    def __init__(self):
        self.security = HTTPBearer()
        self.verify_url = "https://fastapi-auth-4rl3.onrender.com/api/v1/auth/verify"
    
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