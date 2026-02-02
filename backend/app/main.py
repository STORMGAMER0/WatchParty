from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.websocket.routes import router as websocket_router

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Real-time collaborative browsing platform",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.api_v1_prefix)

# Include WebSocket routes
app.include_router(websocket_router)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
    }
