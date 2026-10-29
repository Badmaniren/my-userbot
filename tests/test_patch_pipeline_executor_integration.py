import unittest
import tempfile
import os
import shutil
import subprocess
import uuid
from skills.patch_pipeline_executor import execute_patch_pipeline, PatchPipelineError

class TestPatchPipelineExecutorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        subprocess.run(["git", "init", self.repo_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Test User"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "test@example.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.file_name = f"test_file_{uuid.uuid4().hex[:8]}.txt"
        self.file_path = os.path.join(self.repo_path, self.file_name)

        original_content = "Initial line\n"
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(original_content)

        subprocess.run(["git", "-C", self.repo_path, "add", self.file_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_execute_patch_pipeline_success(self):
        unique_string = f"line_added_{uuid.uuid4().hex}"

        patch_content = (
            f"--- a/{self.file_name}\n"
            f"+++ b/{self.file_name}\n"
            "@@ -1 +1,2 @@\n"
            " Initial line\n"
            f"+{unique_string}\n"
        )
        backup_tag = f"backup_{uuid.uuid4().hex[:6]}"

        result = execute_patch_pipeline(
            repo_path=self.repo_path,
            patch_source=patch_content,
            backup_tag=backup_tag
        )

        self.assertTrue(result)

        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(unique_string, content)

    def test_execute_patch_pipeline_sanitization_error(self):
        invalid_patch_source = None

        with self.assertRaises(PatchPipelineError) as context:
            execute_patch_pipeline(
                repo_path=self.repo_path,
                patch_source=invalid_patch_source
            )

        self.assertIn("Sanitization failed", str(context.exception))

if __name__ == "__main__":
    unittest.main()