
# main.py
# Standard library imports
import asyncio
import logging
import sys

# Third-party imports
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
# Local application imports

from app.db.config import Database
from app.core.config import settings
from app.api.routes.index import router as index_route

# Configure logging
logger = logging.getLogger(__name__)



router = APIRouter()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle events"""
    try:
        # Startup logic
        mongodb = await Database.connect_db()
        if not mongodb:
            logger.error("MongoDB connection failed. Exiting the app.")
            sys.exit(1)

        yield 
        
    finally:
        await Database.close_db()
        

# Initialize FastAPI app with configuration
app = FastAPI(
    lifespan=lifespan,
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="BoardAndGo flight Agent Authentication",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check route
@router.get("/health")
def health_check():
    try:
        return {"status": "ok", "message": "BoardAndGo flight Agent Active"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "message": "Service is not available"}


@router.get("/")
def root():
    try:
        return {"message": "Welcome to BoardAndGo flight tracking api"}
    except Exception as e:
        logger.error(f"App is not running: {e}")
        return {"message": "Service is not available"}
    
# Include API routes
app.include_router(router)
app.include_router(index_route, prefix=settings.API_V1_STR)





