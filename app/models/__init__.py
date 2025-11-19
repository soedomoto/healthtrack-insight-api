from sqlalchemy import Column, DateTime, Integer, String, Date, Text, Float, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base


class User(Base):
    """User model for HealthTrack application with comprehensive health profile."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)

    # Health Profile Fields
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)  # 'male', 'female', 'other', 'prefer_not_to_say'
    marital_status = Column(
        String(50), nullable=True
    )  # 'single', 'married', 'divorced', 'widowed', 'prefer_not_to_say'
    occupation = Column(String(255), nullable=True)
    medical_history = Column(
        Text, nullable=True
    )  # JSON or text for chronic conditions, allergies, past illnesses

    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    health_metrics = relationship(
        "HealthMetric", back_populates="user", cascade="all, delete-orphan"
    )
    health_insights = relationship(
        "HealthInsight", back_populates="user", cascade="all, delete-orphan"
    )
    health_goals = relationship("HealthGoal", back_populates="user", cascade="all, delete-orphan")
    nutrition_logs = relationship(
        "NutritionLog", back_populates="user", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_user_email", "email"),
        Index("idx_user_username", "username"),
        Index("idx_user_created_at", "created_at"),
    )


class HealthMetric(Base):
    """Health metrics model for tracking user health data (exercise, vitals, etc.)."""

    __tablename__ = "health_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Vital Signs: heart_rate, sleep_hours, weight, blood_pressure, blood_glucose, etc.
    # Exercise: steps, distance, calories_burned, intensity, duration, type
    metric_type = Column(String(50), nullable=False, index=True)
    value = Column(String(100), nullable=False)
    unit = Column(String(50), nullable=True)
    intensity = Column(String(20), nullable=True)  # For exercise: 'light', 'moderate', 'vigorous'
    duration = Column(Integer, nullable=True)  # Duration in minutes for exercises

    recorded_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="health_metrics")

    __table_args__ = (
        Index("idx_metric_user_id", "user_id"),
        Index("idx_metric_type", "metric_type"),
        Index("idx_metric_recorded_at", "recorded_at"),
        Index("idx_metric_user_type_recorded", "user_id", "metric_type", "recorded_at"),
    )


class HealthInsight(Base):
    """AI-generated health insights and recommendations for users."""

    __tablename__ = "health_insights"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    title = Column(String(255), nullable=False)
    description = Column(String(2000), nullable=False)
    reasoning = Column(Text, nullable=True)  # Explanation of why this recommendation is made

    insight_type = Column(
        String(50), nullable=False
    )  # 'warning', 'suggestion', 'achievement', 'trend'
    severity = Column(String(20), nullable=True)  # 'low', 'medium', 'high'
    rank = Column(Integer, nullable=True)  # Ranking (1-5) for personalized recommendations

    # Reference to related metrics
    related_metric_type = Column(String(50), nullable=True)

    is_read = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="health_insights")

    __table_args__ = (
        Index("idx_insight_user_id", "user_id"),
        Index("idx_insight_created_at", "created_at"),
        Index("idx_insight_rank", "rank"),
        Index("idx_insight_user_rank", "user_id", "rank"),
    )


class HealthGoal(Base):
    """User health goals (weight loss, better sleep, more exercise, etc.)."""

    __tablename__ = "health_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    goal_type = Column(
        String(100), nullable=False
    )  # 'weight_loss', 'better_sleep', 'more_exercise', 'stress_reduction', etc.
    description = Column(String(500), nullable=True)
    target_value = Column(String(100), nullable=True)
    current_value = Column(String(100), nullable=True)
    unit = Column(String(50), nullable=True)
    target_date = Column(Date, nullable=True)

    status = Column(String(20), default="active")  # 'active', 'completed', 'abandoned'
    priority = Column(String(20), nullable=True)  # 'low', 'medium', 'high'

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="health_goals")

    __table_args__ = (
        Index("idx_goal_user_id", "user_id"),
        Index("idx_goal_status", "status"),
        Index("idx_goal_user_status", "user_id", "status"),
    )


class NutritionLog(Base):
    """Nutrition and diet tracking (meals, water intake, calories, macros)."""

    __tablename__ = "nutrition_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Meal details
    meal_type = Column(String(50), nullable=True)  # 'breakfast', 'lunch', 'dinner', 'snack'
    meal_description = Column(String(500), nullable=True)

    # Nutrition values
    calories = Column(Float, nullable=True)
    protein_grams = Column(Float, nullable=True)
    carbs_grams = Column(Float, nullable=True)
    fat_grams = Column(Float, nullable=True)
    water_intake_ml = Column(Float, nullable=True)

    # Additional details
    notes = Column(Text, nullable=True)
    logged_at = Column(DateTime, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="nutrition_logs")

    __table_args__ = (
        Index("idx_nutrition_user_id", "user_id"),
        Index("idx_nutrition_logged_at", "logged_at"),
        Index("idx_nutrition_user_logged", "user_id", "logged_at"),
    )
