import asyncio
import unittest

from fastapi import BackgroundTasks
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import backend.models  # noqa: F401 - register all SQLAlchemy models
from backend.api.scenarios import _user_scenario_to_response
from backend.api.sentences import continue_conversation, generate_sentence
from backend.database import Base
from backend.models.profile import UserProfile
from backend.models.shared_scenario import SharedScenario
from backend.models.shared_sentence import SharedSentence
from backend.models.user import User
from backend.models.user_scenario import UserScenario
from backend.models.user_sentence_progress import UserSentenceProgress
from backend.schemas import ContinueRequest, SentenceGenerate


class SentenceResumeTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite:///:memory:")
        self.session = sessionmaker(bind=engine)()
        Base.metadata.create_all(engine)
        self.addCleanup(self.session.close)

        self.user = User(username="resume-test-user", password_hash="not-used")
        self.session.add(self.user)
        self.session.flush()
        self.session.add(UserProfile(
            user_id=self.user.id,
            role="daily",
            target_language="en",
            proficiency_level="intermediate",
        ))
        self.shared_scenario = SharedScenario(
            role="daily",
            language="en",
            proficiency_level="intermediate",
            title="Resume test scenario",
            description="",
            context="",
        )
        self.session.add(self.shared_scenario)
        self.session.flush()
        self.user_scenario = UserScenario(
            user_id=self.user.id,
            shared_scenario_id=self.shared_scenario.id,
            session_id="resume-test-session",
        )
        self.root_sentence = SharedSentence(
            shared_scenario_id=self.shared_scenario.id,
            native_text="root",
            target_text="root",
            sentence_order=1,
        )
        self.session.add_all([self.user_scenario, self.root_sentence])
        self.session.commit()

    def test_generated_and_continued_sentences_update_resume_point(self):
        async def exercise_resume_point():
            generated = await generate_sentence(
                SentenceGenerate(scenario_id=self.user_scenario.id),
                BackgroundTasks(),
                self.session,
                self.user,
            )
            self.assertEqual(generated["id"], self.root_sentence.id)
            self.session.refresh(self.user_scenario)
            self.assertEqual(self.user_scenario.last_active_sentence_id, self.root_sentence.id)
            self.assertEqual(
                _user_scenario_to_response(self.user_scenario)["last_active_sentence_id"],
                self.root_sentence.id,
            )

            continuation = SharedSentence(
                shared_scenario_id=self.shared_scenario.id,
                parent_sentence_id=self.root_sentence.id,
                native_text="continuation",
                target_text="continuation",
                sentence_order=0,
            )
            self.session.add(continuation)
            self.session.commit()

            continued = await continue_conversation(
                ContinueRequest(
                    scenario_id=self.user_scenario.id,
                    sentence_id=self.root_sentence.id,
                ),
                self.session,
                self.user,
            )
            self.assertEqual(continued["id"], continuation.id)
            self.session.refresh(self.user_scenario)
            self.assertEqual(self.user_scenario.last_active_sentence_id, continuation.id)

        asyncio.run(exercise_resume_point())

    def test_completed_resume_point_advances_to_next_available_sentence(self):
        next_sentence = SharedSentence(
            shared_scenario_id=self.shared_scenario.id,
            native_text="next",
            target_text="next",
            sentence_order=2,
        )
        self.user_scenario.last_active_sentence_id = self.root_sentence.id
        self.session.add_all([
            next_sentence,
            UserSentenceProgress(
                user_id=self.user.id,
                shared_sentence_id=self.root_sentence.id,
                is_completed=True,
            ),
        ])
        self.session.commit()

        async def advance_from_completed_resume_point():
            generated = await generate_sentence(
                SentenceGenerate(scenario_id=self.user_scenario.id),
                BackgroundTasks(),
                self.session,
                self.user,
            )
            self.assertEqual(generated["id"], next_sentence.id)
            self.session.refresh(self.user_scenario)
            self.assertEqual(self.user_scenario.last_active_sentence_id, next_sentence.id)

        asyncio.run(advance_from_completed_resume_point())


if __name__ == "__main__":
    unittest.main()
