import unittest
import uuid
import random
import os
import tempfile
import shutil
from skills.repo_health_diagnostic import repo_health_diagnostic

class TestRepoHealthDiagnosticIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.unique_id = str(uuid.uuid4())
        self.metric_threshold = random.randint(10, 100)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_repo_health_diagnostic_real_execution(self):
        dummy_file_path = os.path.join(self.test_dir, f"test_{self.unique_id}.py")
        with open(dummy_file_path, "w", encoding="utf-8") as f:
            f.write(f"# Diagnostic test file {self.unique_id}\nprint('Hello, Architecture!')\n")

        result = repo_health_diagnostic(
            repo_path=self.test_dir,
            diagnostic_id=self.unique_id,
            threshold=self.metric_threshold
        )

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("diagnostic_id", result)
        self.assertEqual(result["diagnostic_id"], self.unique_id)
        self.assertIn("metrics", result)
        self.assertTrue(os.path.exists(dummy_file_path))

if __name__ == "__main__":
    unittest.main()