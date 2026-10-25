import unittest
import tempfile
import uuid
from pathlib import Path

from skills.anomaly_autofixer import AnomalyAutofixer, AnomalyAutofixerError
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger
from skills.git_inspector import GitInspector


class TestAnomalyAutofixerIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        self.log_path = str(Path(self.repo_path) / f"audit_{uuid.uuid4()}.log")

        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=10
        )
        self.logger = AnomalyLogger(log_path=self.log_path)
        self.git_inspector = GitInspector(repo_path=self.repo_path)

        self.anti_cheat_token = f"token_{uuid.uuid4()}"
        self.autofixer = AnomalyAutofixer(
            target_path=self.repo_path,
            anti_cheat_token=self.anti_cheat_token,
            audit_hub=self.audit_hub,
            logger=self.logger,
            git_inspector=self.git_inspector
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_apply_patch_integration_success(self):
        random_file_name = f"target_{uuid.uuid4().hex[:8]}.py"
        target_file_path = Path(self.repo_path) / random_file_name

        initial_code = f"# Initial code UUID: {uuid.uuid4()}"
        target_file_path.write_text(initial_code, encoding="utf-8")

        fix_snippet = f"# Fixed snippet UUID: {uuid.uuid4()}"
        patch_content = {
            "file_path": random_file_name,
            "fix_snippet": fix_snippet
        }

        result = self.autofixer.apply_patch(patch_content)
        self.assertTrue(result)

        updated_code = target_file_path.read_text(encoding="utf-8")
        self.assertIn(initial_code, updated_code)
        self.assertIn(fix_snippet, updated_code)

    def test_apply_patch_integration_invalid_dict(self):
        invalid_patch = {
            "file_path": "",
            "fix_snippet": f"snippet_{uuid.uuid4()}"
        }
        with self.assertRaises(AnomalyAutofixerError):
            self.autofixer.apply_patch(invalid_patch)


if __name__ == "__main__":
    unittest.main()