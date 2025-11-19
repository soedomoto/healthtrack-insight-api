"""Health goals endpoints for managing user health objectives."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime
from typing import Optional

from app.db.session import get_db
from app.models import User, HealthGoal
from app.schemas import HealthGoalCreate, HealthGoalUpdate, HealthGoalResponse

router = APIRouter(prefix="/health-goals", tags=["health-goals"])


@router.post("/", response_model=HealthGoalResponse, status_code=status.HTTP_201_CREATED)
async def create_health_goal(
    user_id: int,
    goal: HealthGoalCreate,
    db: AsyncSession = Depends(get_db),
) -> HealthGoalResponse:
    """
    Create a new health goal for a user.

    Supports goal types like:
    - weight_loss: Lose weight (provide target_value in kg/lbs)
    - better_sleep: Improve sleep quality (provide target_value in hours)
    - more_exercise: Increase physical activity (provide target_value in minutes/week)
    - stress_reduction: Reduce stress levels
    - better_nutrition: Improve diet
    - blood_pressure: Lower blood pressure (provide target_value in mmHg)
    - blood_glucose: Manage blood sugar (provide target_value in mg/dL)
    """
    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db_goal = HealthGoal(
        user_id=user_id,
        goal_type=goal.goal_type,
        description=goal.description,
        target_value=goal.target_value,
        unit=goal.unit,
        target_date=goal.target_date,
        priority=goal.priority or "medium",
        status="active",
    )
    db.add(db_goal)
    await db.commit()
    await db.refresh(db_goal)
    return db_goal


@router.get("/{goal_id}", response_model=HealthGoalResponse)
async def get_health_goal(
    goal_id: int,
    db: AsyncSession = Depends(get_db),
) -> HealthGoalResponse:
    """Get a specific health goal."""
    result = await db.execute(select(HealthGoal).where(HealthGoal.id == goal_id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    return goal


@router.get("/user/{user_id}", response_model=list[HealthGoalResponse])
async def get_user_health_goals(
    user_id: int,
    status_filter: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[HealthGoalResponse]:
    """
    Get all health goals for a user.

    Query parameters:
    - status_filter: Filter by status ('active', 'completed', 'abandoned') - optional
    """
    query = select(HealthGoal).where(HealthGoal.user_id == user_id)

    if status_filter:
        query = query.where(HealthGoal.status == status_filter)

    query = query.order_by(HealthGoal.priority.desc(), HealthGoal.created_at.desc())

    result = await db.execute(query)
    goals = result.scalars().all()
    return list(goals)


@router.put("/{goal_id}", response_model=HealthGoalResponse)
async def update_health_goal(
    goal_id: int,
    goal_update: HealthGoalUpdate,
    db: AsyncSession = Depends(get_db),
) -> HealthGoalResponse:
    """
    Update a health goal.

    Can update:
    - description
    - current_value (track progress)
    - status ('active', 'completed', 'abandoned')
    - priority ('low', 'medium', 'high')
    """
    result = await db.execute(select(HealthGoal).where(HealthGoal.id == goal_id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    if goal_update.description is not None:
        goal.description = goal_update.description
    if goal_update.current_value is not None:
        goal.current_value = goal_update.current_value
    if goal_update.status is not None:
        goal.status = goal_update.status
    if goal_update.priority is not None:
        goal.priority = goal_update.priority

    goal.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(goal)
    return goal


@router.delete("/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_health_goal(
    goal_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a health goal."""
    result = await db.execute(select(HealthGoal).where(HealthGoal.id == goal_id))
    goal = result.scalar_one_or_none()
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    await db.delete(goal)
    await db.commit()
    return None
