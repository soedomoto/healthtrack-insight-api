from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


# ==================== USER SCHEMAS ====================


class UserBase(BaseModel):
    """Base user schema."""

    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user (registration)."""

    password: str = Field(..., min_length=8)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    occupation: Optional[str] = None
    medical_history: Optional[str] = None


class UserUpdate(BaseModel):
    """Schema for updating a user profile."""

    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    occupation: Optional[str] = None
    medical_history: Optional[str] = None


class UserResponse(UserBase):
    """Schema for user response."""

    id: int
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None
    occupation: Optional[str] = None
    medical_history: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== HEALTH METRIC SCHEMAS ====================


class HealthMetricBase(BaseModel):
    """Base health metric schema."""

    metric_type: str
    value: str
    unit: Optional[str] = None
    intensity: Optional[str] = None
    duration: Optional[int] = None
    recorded_at: datetime


class HealthMetricCreate(HealthMetricBase):
    """Schema for creating a health metric."""

    pass


class HealthMetricResponse(HealthMetricBase):
    """Schema for health metric response."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== HEALTH GOAL SCHEMAS ====================


class HealthGoalBase(BaseModel):
    """Base health goal schema."""

    goal_type: str
    description: Optional[str] = None
    target_value: Optional[str] = None
    current_value: Optional[str] = None
    unit: Optional[str] = None
    target_date: Optional[date] = None
    priority: Optional[str] = None


class HealthGoalCreate(HealthGoalBase):
    """Schema for creating a health goal."""

    pass


class HealthGoalUpdate(BaseModel):
    """Schema for updating a health goal."""

    description: Optional[str] = None
    current_value: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class HealthGoalResponse(HealthGoalBase):
    """Schema for health goal response."""

    id: int
    user_id: int
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== NUTRITION LOG SCHEMAS ====================


class NutritionLogBase(BaseModel):
    """Base nutrition log schema."""

    meal_type: Optional[str] = None
    meal_description: Optional[str] = None
    calories: Optional[float] = None
    protein_grams: Optional[float] = None
    carbs_grams: Optional[float] = None
    fat_grams: Optional[float] = None
    water_intake_ml: Optional[float] = None
    notes: Optional[str] = None
    logged_at: datetime


class NutritionLogCreate(NutritionLogBase):
    """Schema for creating a nutrition log."""

    pass


class NutritionLogUpdate(BaseModel):
    """Schema for updating a nutrition log."""

    meal_type: Optional[str] = None
    meal_description: Optional[str] = None
    calories: Optional[float] = None
    protein_grams: Optional[float] = None
    carbs_grams: Optional[float] = None
    fat_grams: Optional[float] = None
    water_intake_ml: Optional[float] = None
    notes: Optional[str] = None


class NutritionLogResponse(NutritionLogBase):
    """Schema for nutrition log response."""

    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ==================== HEALTH INSIGHT SCHEMAS ====================


class HealthInsightBase(BaseModel):
    """Base health insight schema."""

    title: str
    description: str
    reasoning: Optional[str] = None
    insight_type: str
    severity: Optional[str] = None


class HealthInsightCreate(HealthInsightBase):
    """Schema for creating a health insight."""

    rank: Optional[int] = None
    related_metric_type: Optional[str] = None


class HealthInsightResponse(HealthInsightBase):
    """Schema for health insight response."""

    id: int
    user_id: int
    rank: Optional[int] = None
    related_metric_type: Optional[str] = None
    is_read: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HealthInsightUpdate(BaseModel):
    """Schema for updating a health insight."""

    is_read: Optional[bool] = None


# ==================== PERSONALIZED RECOMMENDATIONS SCHEMA ====================


class PersonalizedRecommendation(BaseModel):
    """Schema for a single personalized recommendation."""

    rank: int  # 1-5
    title: str
    description: str
    reasoning: str
    action_steps: list[str]
    related_metrics: list[str]
    impact_area: str
    severity: Optional[str] = None


class PersonalizedRecommendationsResponse(BaseModel):
    """Schema for personalized health recommendations (top 5)."""

    user_id: int
    recommendations: list[PersonalizedRecommendation]
    generated_at: datetime
    based_on_period_days: int = 30

    class Config:
        from_attributes = True
