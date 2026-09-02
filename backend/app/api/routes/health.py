from fastapi import APIRouter
from typing import Dict

router = APIRouter(tags=["health"])


@router.get("/api/health")
def health_check() -> Dict[str, str]:
    return {
        "status": "ok",
        "service": "agentic-commerce",
        "version": "1.0.0",
    }
