import unittest
import os
import tempfile
import uuid
from skills.release_automation_hub import ReleaseAutomationHub


class TestReleaseAutomationHubIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.hub = ReleaseAutomationHub(self.repo_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_execute_release_cycle_integration(self):
        unique_id = str(uuid.uuid4())
        report_filename = f"release_report_{unique_id}.txt"
        output_path = os.path.join(self.repo_path, report_filename)

        success = self.hub.execute_release_cycle(output_path)

        self.assertIsInstance(success, bool)
        self.assertTrue(
            os.path.exists(output_path),
            f"Integration failure: Expected report file at {output_path} was not created."
        )

        with open(output_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertGreater(
            len(content), 0,
            "Integration failure: The generated report file is empty."
        )

    def test_execute_release_with_report_integration(self):
        unique_id = str(uuid.uuid4())
        report_filename = f"release_with_report_{unique_id}.log"
        output_path = os.path.join(self.repo_path, report_filename)

        success = self.hub.execute_release_with_report(output_path)

        self.assertIsInstance(success, bool)
        self.assertTrue(
            os.path.exists(output_path),
            f"Integration failure: Expected report file at {output_path} was not created via execute_release_with_report."
        )


if __name__ == "__main__":
    unittest.main()