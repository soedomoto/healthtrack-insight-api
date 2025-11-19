"""
AI-powered Health Insights Engine for generating personalized recommendations.

This engine analyzes user health patterns, metrics, and goals to generate
top 5 actionable, personalized recommendations with context and reasoning.
"""

from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import statistics

from app.models import User, HealthMetric, HealthGoal, NutritionLog, HealthInsight
from app.schemas import PersonalizedRecommendation, PersonalizedRecommendationsResponse


class HealthInsightsEngine:
    """AI-powered health insights generator for HealthTrack."""

    def __init__(self, db: AsyncSession):
        """Initialize the health insights engine."""
        self.db = db
        self.recommendation_rules = self._initialize_rules()

    def _initialize_rules(self) -> dict:
        """Initialize recommendation rules based on health patterns."""
        return {
            "low_step_count": {
                "threshold": 5000,
                "metric_type": "steps",
                "title": "Increase Daily Activity",
                "reasoning_template": "Your daily steps average {value} but recommended is 10,000+",
                "action_steps": [
                    "Start with a 10-minute walk after meals",
                    "Use stairs instead of elevators",
                    "Park further away to increase walking distance",
                    "Try a step-tracking challenge with friends",
                ],
            },
            "insufficient_sleep": {
                "threshold": 7,
                "metric_type": "sleep_hours",
                "title": "Improve Sleep Quality",
                "reasoning_template": "Your average sleep is {value} hours, but 7-9 hours recommended",
                "action_steps": [
                    "Establish a consistent bedtime routine",
                    "Avoid screens 1 hour before bed",
                    "Keep bedroom temperature between 65-68°F",
                    "Limit caffeine after 2 PM",
                ],
            },
            "elevated_heart_rate": {
                "threshold": 85,
                "metric_type": "heart_rate",
                "title": "Reduce Resting Heart Rate",
                "reasoning_template": "Your resting heart rate is {value} bpm, elevated for optimal health",
                "action_steps": [
                    "Practice deep breathing exercises (5 min daily)",
                    "Engage in regular cardio (150 min/week)",
                    "Reduce stress through meditation or yoga",
                    "Limit caffeine and alcohol",
                ],
            },
            "weight_management": {
                "threshold": None,
                "metric_type": "weight",
                "title": "Track Weight Progress",
                "reasoning_template": "Current weight tracking enabled - focus on consistency",
                "action_steps": [
                    "Weigh yourself at same time daily (morning best)",
                    "Track weekly averages instead of daily fluctuations",
                    "Combine with exercise and nutrition logs",
                    "Set realistic 1-2 lbs per week loss target",
                ],
            },
            "poor_nutrition": {
                "threshold": 2000,
                "metric_type": "calories",
                "title": "Improve Daily Nutrition",
                "reasoning_template": "Average daily calories: {value}, consider balanced intake",
                "action_steps": [
                    "Log all meals for one week to establish baseline",
                    "Aim for balance: 50% carbs, 25% protein, 25% fat",
                    "Increase water intake to 8+ glasses daily",
                    "Meal prep on Sundays for the week",
                ],
            },
            "low_water_intake": {
                "threshold": 2000,
                "metric_type": "water_intake_ml",
                "title": "Stay Hydrated",
                "reasoning_template": "Average daily water intake: {value}ml, aim for 2000-3000ml",
                "action_steps": [
                    "Drink glass of water when you wake up",
                    "Set hourly reminders to drink water",
                    "Carry a water bottle throughout the day",
                    "Drink water before, during, and after exercise",
                ],
            },
        }

    async def get_user_metrics_summary(self, user_id: int, days: int = 30) -> dict:
        """Get summary of user metrics for the past N days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        result = await self.db.execute(
            select(HealthMetric).where(
                (HealthMetric.user_id == user_id) & (HealthMetric.recorded_at >= cutoff_date)
            )
        )
        metrics = result.scalars().all()

        # Group metrics by type
        metrics_by_type = {}
        for metric in metrics:
            if metric.metric_type not in metrics_by_type:
                metrics_by_type[metric.metric_type] = []
            try:
                metrics_by_type[metric.metric_type].append(float(metric.value))
            except (ValueError, TypeError):
                pass

        # Calculate statistics for each metric type
        summary = {}
        for metric_type, values in metrics_by_type.items():
            if values:
                summary[metric_type] = {
                    "count": len(values),
                    "average": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "stdev": statistics.stdev(values) if len(values) > 1 else 0,
                    "latest": values[-1],
                }

        return summary

    async def get_user_goals(self, user_id: int) -> list:
        """Get active health goals for user."""
        result = await self.db.execute(
            select(HealthGoal).where(
                (HealthGoal.user_id == user_id) & (HealthGoal.status == "active")
            )
        )
        return result.scalars().all()

    async def get_user_profile(self, user_id: int) -> Optional[User]:
        """Get user profile for personalization."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def generate_personalized_recommendations(
        self, user_id: int, days: int = 30
    ) -> Optional[PersonalizedRecommendationsResponse]:
        """
        Generate top 5 personalized health recommendations for user.

        Args:
            user_id: User ID
            days: Number of days of historical data to analyze

        Returns:
            PersonalizedRecommendationsResponse with top 5 recommendations
        """
        user = await self.get_user_profile(user_id)
        if not user:
            return None

        metrics_summary = await self.get_user_metrics_summary(user_id, days)
        goals = await self.get_user_goals(user_id)

        recommendations = []

        # Rule 1: Low step count
        if "steps" in metrics_summary:
            steps_avg = metrics_summary["steps"]["average"]
            if steps_avg < self.recommendation_rules["low_step_count"]["threshold"]:
                recommendations.append(
                    self._create_recommendation(
                        rank=len(recommendations) + 1,
                        rule="low_step_count",
                        user_age=self._get_user_age(user),
                        metric_value=steps_avg,
                    )
                )

        # Rule 2: Insufficient sleep
        if "sleep_hours" in metrics_summary:
            sleep_avg = metrics_summary["sleep_hours"]["average"]
            if sleep_avg < self.recommendation_rules["insufficient_sleep"]["threshold"]:
                recommendations.append(
                    self._create_recommendation(
                        rank=len(recommendations) + 1,
                        rule="insufficient_sleep",
                        user_age=self._get_user_age(user),
                        metric_value=sleep_avg,
                    )
                )

        # Rule 3: Elevated heart rate
        if "heart_rate" in metrics_summary:
            hr_avg = metrics_summary["heart_rate"]["average"]
            if hr_avg > self.recommendation_rules["elevated_heart_rate"]["threshold"]:
                recommendations.append(
                    self._create_recommendation(
                        rank=len(recommendations) + 1,
                        rule="elevated_heart_rate",
                        user_age=self._get_user_age(user),
                        metric_value=hr_avg,
                    )
                )

        # Rule 4: Weight management (if weight goal exists or tracking active)
        if "weight" in metrics_summary or any(g.goal_type == "weight_loss" for g in goals):
            recommendations.append(
                self._create_recommendation(
                    rank=len(recommendations) + 1,
                    rule="weight_management",
                    user_age=self._get_user_age(user),
                    metric_value=None,
                )
            )

        # Rule 5: Nutrition improvement (if nutrition tracked or exists)
        if "calories" in metrics_summary or any(
            g.goal_type.startswith("better_nutrition") for g in goals
        ):
            calories_avg = metrics_summary.get("calories", {}).get("average")
            recommendations.append(
                self._create_recommendation(
                    rank=len(recommendations) + 1,
                    rule="poor_nutrition",
                    user_age=self._get_user_age(user),
                    metric_value=calories_avg,
                )
            )

        # Rule 6: Water intake
        if "water_intake_ml" in metrics_summary:
            water_avg = metrics_summary["water_intake_ml"]["average"]
            if water_avg < self.recommendation_rules["low_water_intake"]["threshold"]:
                recommendations.append(
                    self._create_recommendation(
                        rank=len(recommendations) + 1,
                        rule="low_water_intake",
                        user_age=self._get_user_age(user),
                        metric_value=water_avg,
                    )
                )

        # Sort by priority and limit to top 5
        recommendations.sort(key=lambda x: x.rank)
        recommendations = recommendations[:5]

        # Update ranks
        for i, rec in enumerate(recommendations, 1):
            rec.rank = i

        return PersonalizedRecommendationsResponse(
            user_id=user_id,
            recommendations=recommendations,
            generated_at=datetime.utcnow(),
            based_on_period_days=days,
        )

    def _get_user_age(self, user: User) -> Optional[int]:
        """Calculate user age from date of birth."""
        if not user.date_of_birth:
            return None
        today = datetime.utcnow().date()
        return (
            today.year
            - user.date_of_birth.year
            - ((today.month, today.day) < (user.date_of_birth.month, user.date_of_birth.day))
        )

    def _create_recommendation(
        self,
        rank: int,
        rule: str,
        user_age: Optional[int],
        metric_value: Optional[float],
    ) -> PersonalizedRecommendation:
        """Create a personalized recommendation from a rule."""
        rule_config = self.recommendation_rules[rule]

        # Personalize based on user age if available
        action_steps = rule_config["action_steps"].copy()
        if user_age and user_age > 60 and rule == "low_step_count":
            action_steps.insert(0, "Consider low-impact activities like swimming")

        reasoning = rule_config["reasoning_template"]
        if metric_value is not None:
            reasoning = reasoning.format(value=f"{metric_value:.1f}")

        # Determine related metrics
        related_metrics = [rule_config["metric_type"]]

        return PersonalizedRecommendation(
            rank=rank,
            title=rule_config["title"],
            description=f"Based on your health data from the past 30 days, we recommend focusing on this area",
            reasoning=reasoning,
            action_steps=action_steps,
            related_metrics=related_metrics,
            impact_area=rule_config["metric_type"],
            severity=(
                "medium" if metric_value is None else ("high" if metric_value > 1.5 else "medium")
            ),
        )
