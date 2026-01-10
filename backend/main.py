"""FastAPI backend for Ugolki game."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from backend.models.database import init_db
from backend.api.auth import router as auth_router
from backend.api.leaderboard import router as leaderboard_router
from backend.api.game_websocket import websocket_handler


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    await init_db()
    yield


app = FastAPI(
    title="Ugolki Game API",
    description="Backend API for the Ugolki board game",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
# In production, ALLOWED_ORIGINS should be set to your domain(s)
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS", 
    "http://localhost:5173,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(leaderboard_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.websocket("/ws/game")
async def game_websocket(websocket: WebSocket, token: str):
    """WebSocket endpoint for game communication."""
    await websocket_handler(websocket, token)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
