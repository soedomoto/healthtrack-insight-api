"""Nutrition logging endpoints for tracking meals, water intake, and calories."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from app.db.session import get_db
from app.models import User, NutritionLog
from app.schemas import NutritionLogCreate, NutritionLogUpdate, NutritionLogResponse

router = APIRouter(prefix="/nutrition-logs", tags=["nutrition"])


@router.post("/", response_model=NutritionLogResponse, status_code=status.HTTP_201_CREATED)
async def log_nutrition(
    user_id: int,
    nutrition: NutritionLogCreate,
    db: AsyncSession = Depends(get_db),
) -> NutritionLogResponse:
    """
    Log a nutrition entry for a user.

    Supports tracking:
    - meal_type: Type of meal ('breakfast', 'lunch', 'dinner', 'snack')
    - meal_description: What was eaten
    - calories: Total calories
    - macros: protein_grams, carbs_grams, fat_grams
    - water_intake_ml: Water consumed in milliliters
    - notes: Additional notes
    """
    # Verify user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    db_nutrition = NutritionLog(
        user_id=user_id,
        meal_type=nutrition.meal_type,
        meal_description=nutrition.meal_description,
        calories=nutrition.calories,
        protein_grams=nutrition.protein_grams,
        carbs_grams=nutrition.carbs_grams,
        fat_grams=nutrition.fat_grams,
        water_intake_ml=nutrition.water_intake_ml,
        notes=nutrition.notes,
        logged_at=nutrition.logged_at,
    )
    db.add(db_nutrition)
    await db.commit()
    await db.refresh(db_nutrition)
    return db_nutrition


@router.get("/{log_id}", response_model=NutritionLogResponse)
async def get_nutrition_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
) -> NutritionLogResponse:
    """Get a specific nutrition log entry."""
    result = await db.execute(select(NutritionLog).where(NutritionLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nutrition log not found",
        )
    return log


@router.get("/user/{user_id}", response_model=list[NutritionLogResponse])
async def get_user_nutrition_logs(
    user_id: int,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> list[NutritionLogResponse]:
    """
    Get all nutrition logs for a user (most recent first).

    Query parameters:
    - limit: Maximum records to return (default: 50)
    """
    result = await db.execute(
        select(NutritionLog)
        .where(NutritionLog.user_id == user_id)
        .order_by(NutritionLog.logged_at.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return list(logs)


@router.put("/{log_id}", response_model=NutritionLogResponse)
async def update_nutrition_log(
    log_id: int,
    nutrition_update: NutritionLogUpdate,
    db: AsyncSession = Depends(get_db),
) -> NutritionLogResponse:
    """Update a nutrition log entry."""
    result = await db.execute(select(NutritionLog).where(NutritionLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nutrition log not found",
        )

    # Update only provided fields
    if nutrition_update.meal_type is not None:
        log.meal_type = nutrition_update.meal_type
    if nutrition_update.meal_description is not None:
        log.meal_description = nutrition_update.meal_description
    if nutrition_update.calories is not None:
        log.calories = nutrition_update.calories
    if nutrition_update.protein_grams is not None:
        log.protein_grams = nutrition_update.protein_grams
    if nutrition_update.carbs_grams is not None:
        log.carbs_grams = nutrition_update.carbs_grams
    if nutrition_update.fat_grams is not None:
        log.fat_grams = nutrition_update.fat_grams
    if nutrition_update.water_intake_ml is not None:
        log.water_intake_ml = nutrition_update.water_intake_ml
    if nutrition_update.notes is not None:
        log.notes = nutrition_update.notes

    log.updated_at = datetime.utcnow()

    await db.commit()
    await db.refresh(log)
    return log


@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_nutrition_log(
    log_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Delete a nutrition log entry."""
    result = await db.execute(select(NutritionLog).where(NutritionLog.id == log_id))
    log = result.scalar_one_or_none()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nutrition log not found",
        )

    await db.delete(log)
    await db.commit()
    return None
