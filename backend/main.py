"""
LUNAR GUARDIANS — Junior Astronaut Mission Trainer
FastAPI Backend — Entry Point

This is the main application file. The game API will be built here.
NASA DONKI and other NASA API integrations will be added in Phase 1.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="LUNAR GUARDIANS API",
    description="Backend API for the LUNAR GUARDIANS educational space simulation.",
    version="0.1.0",
)

# Allow requests from the React frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "project": "LUNAR GUARDIANS",
        "version": "0.1.0",
        "status": "Backend is running.",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "ok"}
