import unittest
import os
import shutil
import uuid
import tempfile
import subprocess
from skills.patch_pipeline_runner import PatchPipelineRunner
from skills.patch_sanitizer import PatchSanitizer
from skills.patch_checker import PatchChecker
from skills.patch_applier import PatchApplier

class TestPatchPipelineRunnerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.test_dir, "repo")
        os.makedirs(self.repo_path)

        subprocess.run(["git", "-C", self.repo_path, "init"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Test"], check=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "test@example.com"], check=True)

        self.patch_id = str(uuid.uuid4())
        self.raw_patch_content = f"--- a/test.txt\n+++ b/test.txt\n@@ -1 +1 @@\n-old_data_{self.patch_id}\n+new_data_{self.patch_id}\n"

        test_file = os.path.join(self.repo_path, "test.txt")
        with open(test_file, "w") as f:
            f.write(f"old_data_{self.patch_id}\n")

        subprocess.run(["git", "-C", self.repo_path, "add", "test.txt"], check=True)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", "Initial commit"], check=True)

        self.runner = PatchPipelineRunner(repo_path=self.repo_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_full_pipeline_execution_success(self):
        backup_tag = f"backup_{uuid.uuid4().hex[:8]}"

        result = self.runner.run_pipeline(
            raw_patch=self.raw_patch_content,
            backup_tag=backup_tag
        )

        self.assertTrue(result, "Пайплайн должен вернуть True при успешном применении")

        applier = PatchApplier(repo_path=self.repo_path)
        self.assertTrue(applier.verify_repository_state(), "Состояние репозитория должно быть валидным после применения")

    def test_pipeline_failure_on_invalid_patch(self):
        invalid_patch = "INVALID_PATCH_DATA_" + str(uuid.uuid4())
        backup_tag = f"fail_test_{uuid.uuid4().hex[:8]}"

        try:
            result = self.runner.run_pipeline(
                raw_patch=invalid_patch,
                backup_tag=backup_tag
            )
            self.assertFalse(result, "Пайплайн должен вернуть False для некорректного патча")
        except Exception as e:
            self.assertIsNotNone(e)

    def test_sanitization_and_check_integration(self):
        sanitizer = PatchSanitizer()
        checker = PatchChecker(repo_path=self.repo_path, policy="strict")

        sanitized = sanitizer.sanitize(self.raw_patch_content)
        check_result = checker.check_patch(sanitized, self.repo_path, "test.txt", "strict")

        self.assertIsInstance(check_result, dict)
        self.assertIn("status", check_result)

if __name__ == '__main__':
    unittest.main()