# app/api/__init__.py
"""
API package initialization.
"""
from fastapi import APIRouter

from app.api.agents.endpoints.tiktok import router as tiktok_router

api_router = APIRouter()
api_router.include_router(tiktok_router, prefix="/tiktok", tags=["tiktok"])

# app/api/agents/__init__.py
"""
Agents package initialization.
"""

# app/api/agents/endpoints/__init__.py
"""
API endpoints package initialization.
"""

# app/api/agents/services/__init__.py
"""
Services package initialization.
"""

# app/api/utils/__init__.py
"""
Utilities package initialization.
"""