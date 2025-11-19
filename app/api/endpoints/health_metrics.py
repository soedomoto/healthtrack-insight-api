from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models import User, HealthMetric
from app.schemas import (
    HealthMetricCreate,
    HealthMetricResponse,
)

router = APIRouter(prefix="/health-metrics", tags=["health-metrics"])


@router.post("/", response_model=HealthMetricResponse, status_code=status.HTTP_201_CREATED)
async def create_health_metric(
    user_id: int,
    metric: HealthMetricCreate,
    db: AsyncSession = Depends(get_db),
) -> HealthMetricResponse:
    """Create a new health metric."""
    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    db_metric = HealthMetric(
        user_id=user_id,
        metric_type=metric.metric_type,
        value=metric.value,
        unit=metric.unit,
        recorded_at=metric.recorded_at,
    )
    db.add(db_metric)
    await db.commit()
    await db.refresh(db_metric)
    return db_metric


@router.get("/{metric_id}", response_model=HealthMetricResponse)
async def get_health_metric(
    metric_id: int,
    db: AsyncSession = Depends(get_db),
) -> HealthMetricResponse:
    """Get a specific health metric."""
    result = await db.execute(select(HealthMetric).where(HealthMetric.id == metric_id))
    metric = result.scalar_one_or_none()
    if not metric:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Metric not found")
    return metric


@router.get("/user/{user_id}", response_model=list[HealthMetricResponse])
async def get_user_health_metrics(
    user_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[HealthMetricResponse]:
    """Get all health metrics for a user."""
    result = await db.execute(
        select(HealthMetric)
        .where(HealthMetric.user_id == user_id)
        .order_by(HealthMetric.recorded_at.desc())
    )
    metrics = result.scalars().all()
    return list(metrics)
