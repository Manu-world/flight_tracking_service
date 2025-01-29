
from fastapi import HTTPException, Security, Depends

from app.core.auth import AuthMiddleware

# Create an instance of the middleware
auth_handler = AuthMiddleware()

# Dependency to be used in routes
async def get_current_user(
    user_details: dict = Depends(auth_handler.verify_token)
) -> dict:
    """
    Dependency that returns the current authenticated user's details
    """
    if not user_details:
        raise HTTPException(
            status_code=401,
            detail="Could not validate credentials"
        )
    return user_details