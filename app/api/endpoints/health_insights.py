from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models import User, HealthInsight
from app.schemas import (
    HealthInsightCreate,
    HealthInsightResponse,
    HealthInsightUpdate,
)

router = APIRouter(prefix="/health-insights", tags=["health-insights"])


@router.post("/", response_model=HealthInsightResponse, status_code=status.HTTP_201_CREATED)
async def create_health_insight(
    user_id: int,
    insight: HealthInsightCreate,
    db: AsyncSession = Depends(get_db),
) -> HealthInsightResponse:
    """Create a new health insight for a user."""
    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_insight = HealthInsight(
        user_id=user_id,
        title=insight.title,
        description=insight.description,
        insight_type=insight.insight_type,
        severity=insight.severity,
    )
    db.add(db_insight)
    await db.commit()
    await db.refresh(db_insight)
    return db_insight


@router.get("/{insight_id}", response_model=HealthInsightResponse)
async def get_health_insight(
    insight_id: int,
    db: AsyncSession = Depends(get_db),
) -> HealthInsightResponse:
    """Get a specific health insight."""
    result = await db.execute(select(HealthInsight).where(HealthInsight.id == insight_id))
    insight = result.scalar_one_or_none()
    if not insight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")
    return insight


@router.get("/user/{user_id}", response_model=list[HealthInsightResponse])
async def get_user_health_insights(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[HealthInsightResponse]:
    """Get all health insights for a user."""
    result = await db.execute(
        select(HealthInsight)
        .where(HealthInsight.user_id == user_id)
        .order_by(HealthInsight.created_at.desc())
    )
    insights = result.scalars().all()
    return list(insights)


@router.patch("/{insight_id}", response_model=HealthInsightResponse)
async def update_health_insight(
    insight_id: int,
    insight_update: HealthInsightUpdate,
    db: AsyncSession = Depends(get_db),
) -> HealthInsightResponse:
    """Update a health insight."""
    result = await db.execute(select(HealthInsight).where(HealthInsight.id == insight_id))
    insight = result.scalar_one_or_none()
    if not insight:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Insight not found")

    if insight_update.is_read is not None:
        setattr(insight, "is_read", int(insight_update.is_read))

    await db.commit()
    await db.refresh(insight)
    return insight
