import unittest
import uuid
import random
import os
import tempfile
from skills.repo_performance_profiler import profile_repository
from skills.repo_analytics import analyze_repository
from skills.repo_logger import log_event

class TestRepoPerformanceprofilerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.run_id = str(uuid.uuid4())
        self.metric_threshold = random.randint(50, 500)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_performance_profiler_integration(self):
        dummy_file_name = f"test_artifact_{uuid.uuid4()}.txt"
        dummy_file_path = os.path.join(self.test_dir.name, dummy_file_name)
        
        file_size = random.randint(102, 1024)
        with open(dummy_file_path, "wb") as f:
            f.write(os.urandom(file_size))

        log_event(self.run_id, "Initialized test environment for profiling")

        analytics_result = analyze_repository(self.test_dir.name)
        self.assertIsNotNone(analytics_result)

        profiling_output = profile_repository(
            repo_path=self.test_dir.name,
            session_id=self.run_id,
            threshold=self.metric_threshold
        )

        self.assertIsInstance(profiling_output, dict)
        self.assertIn("profile_id", profiling_output)
        self.assertEqual(profiling_output["session_id"], self.run_id)

        expected_report_path = os.path.join(self.test_dir.name, f"performance_report_{self.run_id}.json")
        self.assertTrue(os.path.exists(expected_report_path), "Integration failed: Profiling report file was not created.")

        with open(expected_report_path, "r", encoding="utf-8") as report_file:
            content = report_file.read()
            self.assertIn(self.run_id, content)

if __name__ == "__main__":
    unittest.main()