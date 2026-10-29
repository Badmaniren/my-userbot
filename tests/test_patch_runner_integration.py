import unittest
import uuid
import random
import os
import tempfile
from skills.patch_runner import PatchRunner, PatchRunnerError, run_patch
from skills.patch_sanitizer import PatchSanitizer
from skills.patch_checker import PatchChecker
from skills.patch_applier import PatchApplier

class TestPatchRunnerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        import subprocess
        subprocess.run(["git", "init", self.repo_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Test User"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "test@example.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.runner = PatchRunner(repo_path=self.repo_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_run_patch_success_and_execution(self):
        unique_id = str(uuid.uuid4())
        marker_text = f"MARKER_{unique_id}"

        target_file_name = f"test_file_{random.randint(1000, 9999)}.txt"
        target_file_path = os.path.join(self.repo_path, target_file_name)

        with open(target_file_path, "w", encoding="utf-8") as f:
            f.write("Initial content\n")

        patch_content = f"""--- {target_file_name}
+++ {target_file_name}
@@ -1,1 +1,2 @@
 Initial content
+{marker_text}
"""

        result_status = self.runner.run_patch(patch_content)
        self.assertTrue(result_status)

        with open(target_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(marker_text, content)

        cmd_output = self.runner.execute_command(["git", "status"])
        self.assertIsInstance(cmd_output, str)

    def test_integration_convenience_function(self):
        unique_id = str(uuid.uuid4())
        target_file_name = f"conv_file_{random.randint(1000, 9999)}.txt"
        target_file_path = os.path.join(self.repo_path, target_file_name)

        with open(target_file_path, "w", encoding="utf-8") as f:
            f.write("Base line\n")

        patch_content = f"""--- {target_file_name}
+++ {target_file_name}
@@ -1,1 +1,2 @@
 Base line
+{unique_id}
"""

        patch_file_fd, patch_file_path = tempfile.mkstemp(suffix=".patch")
        os.close(patch_file_fd)

        try:
            with open(patch_file_path, "w", encoding="utf-8") as f:
                f.write(patch_content)

            status = run_patch(patch_file_path, repo_path=self.repo_path)
            self.assertTrue(status)

            with open(target_file_path, "r", encoding="utf-8") as f:
                updated_content = f.read()
            self.assertIn(unique_id, updated_content)
        finally:
            if os.path.exists(patch_file_path):
                os.remove(patch_file_path)

    def test_integration_invalid_patch_raises_error(self):
        invalid_patch_content = f"INVALID_PATCH_DATA_{uuid.uuid4()}"

        with self.assertRaises(PatchRunnerError):
            self.runner.run_patch(invalid_patch_content)

    def test_integration_execute_command_failure(self):
        invalid_cmd = ["git", f"nonexistent_command_{uuid.uuid4()}"]
        with self.assertRaises(PatchRunnerError):
            self.runner.execute_command(invalid_cmd)

if __name__ == "__main__":
    unittest.main()