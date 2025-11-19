from fastapi import APIRouter

from app.api.endpoints import (
    router,
    health_metrics,
    health_insights,
    users,
    health_goals,
    nutrition_logs,
    recommendations,
)

api_router = APIRouter(prefix="/api/v1")

# Include routers
api_router.include_router(router)
api_router.include_router(users.router)
api_router.include_router(health_metrics.router)
api_router.include_router(health_goals.router)
api_router.include_router(nutrition_logs.router)
api_router.include_router(health_insights.router)
api_router.include_router(recommendations.router)
