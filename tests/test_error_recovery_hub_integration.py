import unittest
import uuid
import random
import os
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from skills.error_recovery_hub import ErrorRecoveryHub

class TestErrorRecoveryHubIntegration(unittest.TestCase):
    def setUp(self):
        self.hub = ErrorRecoveryHub()
        self.test_id = str(uuid.uuid4())
        self.random_error_code = random.randint(1000, 9999)
        self.error_message = f"Integration test error {self.test_id} with code {self.random_error_code}"
        self.module_name = f"test_module_{uuid.uuid4().hex[:8]}"

    def test_error_recovery_lifecycle(self):
        try:
            raise RuntimeError(self.error_message)
        except RuntimeError as e:
            exception_instance = e

        analysis_result = self.hub.analyze_and_recover(
            module_name=self.module_name,
            exception=exception_instance,
            context={"test_id": self.test_id, "code": self.random_error_code}
        )

        self.assertIsInstance(analysis_result, dict)
        self.assertIn("incident_id", analysis_result)
        self.assertEqual(analysis_result["incident_id"], self.test_id)
        
        self.assertIn("patch_generated", analysis_result)
        self.assertTrue(analysis_result["patch_generated"])

        self.assertIn("patch_path", analysis_result)
        patch_file_path = analysis_result["patch_path"]
        
        self.assertTrue(os.path.exists(patch_file_path), f"Patch file was not created at {patch_file_path}")

        with open(patch_file_path, "r", encoding="utf-8") as f:
            patch_content = f.read()

        self.assertIn(self.test_id, patch_content)
        self.assertIn(self.module_name, patch_content)

        logs = self.hub.get_incident_logs(self.test_id)
        self.assertIsInstance(logs, dict)
        self.assertEqual(logs.get("status"), "recovered")

    def tearDown(self):
        potential_patch = Path(f"patches/{self.module_name}_patch.py")
        if potential_patch.exists():
            potential_patch.unlink()
        if potential_patch.parent.exists() and not any(potential_patch.parent.iterdir()):
            potential_patch.parent.rmdir()

if __name__ == "__main__":
    unittest.main()