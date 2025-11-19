from fastapi import APIRouter

router = APIRouter()

# Health check endpoint
@router.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "message": "HealthTrack API is running"}
