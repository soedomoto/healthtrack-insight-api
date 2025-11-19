#!/usr/bin/env python3
"""Database seeding script for development."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal, engine, Base
from app.models import User, HealthMetric, HealthInsight


async def seed_database():
    """Seed the database with sample data."""
    async with AsyncSessionLocal() as session:
        # Create tables if they don't exist
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        print("📊 Seeding database with sample data...")

        # Check if users already exist
        result = await session.execute(select(User).limit(1))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print("✓ Database already seeded. Skipping...")
            return

        # Create sample users
        users_data = [
            {
                "email": "john.doe@healthtrack.local",
                "username": "johndoe",
                "full_name": "John Doe",
                "hashed_password": "$2b$12$eIkmYUfI4sYDzxRSvDm5oOQUKGLQNrLQT7f3v.jtdGBQmcN5kYSgK",  # password
            },
            {
                "email": "jane.smith@healthtrack.local",
                "username": "janesmith",
                "full_name": "Jane Smith",
                "hashed_password": "$2b$12$eIkmYUfI4sYDzxRSvDm5oOQUKGLQNrLQT7f3v.jtdGBQmcN5kYSgK",
            },
        ]

        users = []
        for user_data in users_data:
            user = User(**user_data, is_active=1)
            session.add(user)
            users.append(user)

        await session.flush()  # Flush to get IDs

        # Create sample health metrics
        metrics_data = [
            {
                "user_id": users[0].id,
                "metric_type": "heart_rate",
                "value": "72",
                "unit": "bpm",
                "recorded_at": datetime.utcnow(),
            },
            {
                "user_id": users[0].id,
                "metric_type": "steps",
                "value": "8432",
                "unit": "steps",
                "recorded_at": datetime.utcnow(),
            },
            {
                "user_id": users[0].id,
                "metric_type": "sleep",
                "value": "7.5",
                "unit": "hours",
                "recorded_at": datetime.utcnow(),
            },
            {
                "user_id": users[1].id,
                "metric_type": "heart_rate",
                "value": "68",
                "unit": "bpm",
                "recorded_at": datetime.utcnow(),
            },
        ]

        for metric_data in metrics_data:
            metric = HealthMetric(**metric_data)
            session.add(metric)

        # Create sample health insights
        insights_data = [
            {
                "user_id": users[0].id,
                "title": "Great Activity Level",
                "description": "Your activity level is excellent! You've maintained a consistent exercise routine.",
                "insight_type": "achievement",
                "severity": None,
                "is_read": 0,
            },
            {
                "user_id": users[0].id,
                "title": "Stay Hydrated",
                "description": "Based on your heart rate patterns, remember to drink more water throughout the day.",
                "insight_type": "suggestion",
                "severity": "low",
                "is_read": 0,
            },
            {
                "user_id": users[1].id,
                "title": "Rest Day Recommended",
                "description": "Your recovery metrics suggest you could benefit from a rest day.",
                "insight_type": "suggestion",
                "severity": "medium",
                "is_read": 0,
            },
        ]

        for insight_data in insights_data:
            insight = HealthInsight(**insight_data)
            session.add(insight)

        await session.commit()

        print("✓ Successfully seeded database!")
        print(f"  - Created {len(users)} users")
        print(f"  - Created {len(metrics_data)} health metrics")
        print(f"  - Created {len(insights_data)} health insights")


async def main():
    """Main entry point."""
    try:
        await seed_database()
    except Exception as e:
        print(f"❌ Error seeding database: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
