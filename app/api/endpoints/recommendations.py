"""Personalized health recommendations endpoint."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas import PersonalizedRecommendationsResponse
from app.core.cache import (
    get_cache,
    get_recommendations_cache_key,
)
from scripts.insights_engine import HealthInsightsEngine

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/{user_id}", response_model=PersonalizedRecommendationsResponse)
async def get_personalized_recommendations(
    user_id: int,
    days: int = 30,
    use_cache: bool = True,
    db: AsyncSession = Depends(get_db),
) -> PersonalizedRecommendationsResponse:
    """
    Generate top 5 personalized health recommendations for a user.

    This endpoint analyzes:
    - User health metrics (exercise, vitals, sleep, nutrition)
    - Active health goals
    - User preferences and profile (age, gender, medical history)
    - 30-day health history patterns

    Returns:
    - Ranked recommendations (1-5) with reasoning
    - Specific actionable steps for each recommendation
    - Context about user's health patterns
    - Related metrics and impact areas

    Query parameters:
    - days: Number of days of history to analyze (default: 30)
    - use_cache: Use cached recommendations if available (default: true)

    Performance:
    - With caching: ~50ms response time
    - Without caching: ~500-1000ms response time
    - Cache TTL: 1 hour
    - Cache hit rate target: 80-90%
    """
    # Try cache first
    cache_key = get_recommendations_cache_key(user_id, days)
    if use_cache:
        cache = await get_cache()
        cached = await cache.get(cache_key)
        if cached:
            return PersonalizedRecommendationsResponse(**cached)

    # Generate fresh recommendations
    engine = HealthInsightsEngine(db)
    recommendations = await engine.generate_personalized_recommendations(user_id=user_id, days=days)

    if recommendations is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Cache the result
    if use_cache:
        cache = await get_cache()
        await cache.set(
            cache_key,
            recommendations.model_dump(),
            expire=3600,  # 1 hour cache
        )

    return recommendations
