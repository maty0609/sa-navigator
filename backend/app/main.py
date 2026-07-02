"""SA Navigator API — FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import api_keys, auth, opportunities
from app.config import settings
from app.database import init_db
from app.middleware import InputSanitizationMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown (nothing needed for now)


app = FastAPI(
    title="SA Navigator API",
    description=(
        "Opportunity management backend for the SA Navigator dashboard. "
        "Supports JWT authentication for humans and API key authentication "
        "for agents (OpenClaw, Hermes). See /docs for interactive API documentation."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

# CORS — explicit methods and headers for security
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "Accept"],
)

# Input sanitization — strips null bytes and control chars from JSON bodies
app.add_middleware(InputSanitizationMiddleware)

# Register routers
app.include_router(auth.router)
app.include_router(api_keys.router)
app.include_router(opportunities.router)
