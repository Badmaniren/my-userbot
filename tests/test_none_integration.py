import unittest
import uuid
import random
import time
from skills.none import start_new
from skills import db_storage

class RealIntegrationTestNoneModule(unittest.TestCase):
    def test_start_new_epic_completed_pause(self):
        random_epic_id = f"epic_{uuid.uuid4()}"

        class RealDatabaseStub:
            def __init__(self, epic_id):
                self.epic_id = epic_id

            def fetch_epic_state(self):
                return {
                    "epic_id": self.epic_id,
                    "status": "completed"
                }

        db_instance = RealDatabaseStub(random_epic_id)

        start_time = time.time()
        result = start_new(db_storage=db_instance)
        duration = time.time() - start_time

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "paused")
        self.assertEqual(result.get("epic_id"), random_epic_id)
        self.assertGreaterEqual(duration, 1.0, "Ожидается задержка (пауза) минимум в 1 секунду")

    def test_start_new_epic_in_progress(self):
        random_epic_id = f"epic_{uuid.uuid4()}"
        random_statuses = ["in_progress", "active", "pending", "running"]
        chosen_status = random.choice(random_statuses)

        class RealDatabaseStub:
            def __init__(self, epic_id, status):
                self.epic_id = epic_id
                self.status = status

            def fetch_epic_state(self):
                return {
                    "epic_id": self.epic_id,
                    "status": self.status
                }

        db_instance = RealDatabaseStub(random_epic_id, chosen_status)

        start_time = time.time()
        result = start_new(db_storage=db_instance)
        duration = time.time() - start_time

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), chosen_status)
        self.assertEqual(result.get("epic_id"), random_epic_id)
        self.assertLess(duration, 0.5, "При не завершенном эпике задержка не требуется")

    def test_start_new_no_database(self):
        result = start_new(db_storage=None)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "ready")

if __name__ == "__main__":
    unittest.main()