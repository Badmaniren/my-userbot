import unittest
import tempfile
import os
import shutil
import uuid
from skills.patch_pipeline_orchestrator import PatchPipelineOrchestrator, PatchPipelineError


class TestPatchPipelineOrchestratorIntegration(unittest.TestCase):
    def setUp(self):
        import subprocess
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        self.target_file_name = f"test_file_{uuid.uuid4().hex}.txt"
        self.target_file_path = os.path.join(self.repo_path, self.target_file_name)

        self.unique_content = f"Initial content {uuid.uuid4().hex}"
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(self.unique_content + "\n")

        subprocess.run(["git", "init"], cwd=self.repo_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.repo_path, capture_output=True, check=True)
        subprocess.run(["git", "add", "."], cwd=self.repo_path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", "initial commit"], cwd=self.repo_path, capture_output=True, check=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pipeline_success_flow(self):
        unique_patch_marker = f"patch_marker_{uuid.uuid4().hex}"

        patch_content = f"""--- {self.target_file_name}
+++ {self.target_file_name}
@@ -1,1 +1,1 @@
-{self.unique_content}
+{unique_patch_marker}
"""
        patch_file_path = os.path.join(self.test_dir, f"patch_{uuid.uuid4().hex}.patch")
        with open(patch_file_path, "w", encoding="utf-8") as f:
            f.write(patch_content)

        orchestrator = PatchPipelineOrchestrator(
            repo_path=self.repo_path,
            policy="strict",
            backup_tag=f"backup_{uuid.uuid4().hex[:8]}"
        )

        result = orchestrator.process_patch(patch_file_path, self.target_file_name)
        self.assertTrue(result)

        with open(self.target_file_path, "r", encoding="utf-8") as f:
            updated_content = f.read()

        self.assertIn(unique_patch_marker, updated_content)

    def test_pipeline_failure_on_bad_check(self):
        bad_patch_content = f"""--- non_existent_{uuid.uuid4().hex}.txt
+++ non_existent_{uuid.uuid4().hex}.txt
@@ -0,0 +1,1 @@
+malicious or invalid content {uuid.uuid4().hex}
"""
        patch_file_path = os.path.join(self.test_dir, f"bad_patch_{uuid.uuid4().hex}.patch")
        with open(patch_file_path, "w", encoding="utf-8") as f:
            f.write(bad_patch_content)

        orchestrator = PatchPipelineOrchestrator(
            repo_path=self.repo_path,
            policy="strict",
            backup_tag=f"backup_{uuid.uuid4().hex[:8]}"
        )

        with self.assertRaises(PatchPipelineError):
            orchestrator.process_patch(patch_file_path, "non_existent_target.txt")


if __name__ == "__main__":
    unittest.main()