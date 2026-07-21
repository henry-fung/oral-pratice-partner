import asyncio
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.models  # noqa: F401 - register all SQLAlchemy models
from backend.api.scenarios import generate_scenarios
from backend.database import Base
from backend.models.profile import UserProfile
from backend.models.shared_scenario import SharedScenario
from backend.models.user import User
from backend.schemas import ScenarioGenerate


class ScenarioRefreshTests(unittest.TestCase):
    def test_refresh_does_not_repeat_a_seen_scenario_within_dedup_window(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        session = sessionmaker(bind=engine)()
        self.addCleanup(session.close)

        user = User(username="refresh-test-user", password_hash="not-used")
        session.add(user)
        session.flush()
        session.add(UserProfile(
            user_id=user.id,
            role="daily",
            target_language="en",
            proficiency_level="intermediate",
        ))
        session.add_all([
            SharedScenario(
                role="daily",
                language="en",
                proficiency_level="intermediate",
                title=f"Scenario {index}",
                description="",
                context="",
            )
            for index in range(15)
        ])
        session.commit()

        async def refresh_three_times():
            first = await generate_scenarios(ScenarioGenerate(count=5), session, user)
            second = await generate_scenarios(ScenarioGenerate(count=5), session, user)
            third = await generate_scenarios(ScenarioGenerate(count=5), session, user)
            return ({item["title"] for item in first}, {item["title"] for item in second}, {item["title"] for item in third})

        first_titles, second_titles, third_titles = asyncio.run(refresh_three_times())

        self.assertFalse(first_titles & second_titles)
        self.assertFalse(first_titles & third_titles)
        self.assertFalse(second_titles & third_titles)


if __name__ == "__main__":
    unittest.main()
