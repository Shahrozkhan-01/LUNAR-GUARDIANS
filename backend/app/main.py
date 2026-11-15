"""
LUNAR GUARDIANS — Junior Astronaut Mission Trainer
FastAPI Simulation Application Entry Point (app/main.py)
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes.datasets import router as datasets_router
from app.routes.game import router as game_router
from app.routes.nasa import router as nasa_router

app = FastAPI(
    title="LUNAR GUARDIANS Simulation API",
    description=(
        "Authoritative simulation backend for LUNAR GUARDIANS. "
        "All gameplay units are fictional SIMULATED GAME UNITS."
    ),
    version="0.2.0",
)

frontend_origins = [
    origin.strip()
    for origin in os.environ.get(
        "FRONTEND_URL",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=frontend_origins,
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(game_router)
app.include_router(nasa_router)
app.include_router(datasets_router)


@app.get("/")
def root():
    return {
        "project": "LUNAR GUARDIANS",
        "version": "0.2.0",
        "status": "Simulation backend is running.",
        "data_notice": (
            "NASA DONKI observations are real; gameplay values and consequences "
            "are simulated game units."
        ),
        "docs": "/docs",
    }


@app.get("/health")
@app.get("/api/health")
async def health_check():
    return {"status": "ok"}
