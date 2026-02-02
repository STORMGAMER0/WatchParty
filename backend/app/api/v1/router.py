from fastapi import APIRouter

from app.api.v1.endpoints import auth, rooms

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router)
api_router.include_router(rooms.router)
