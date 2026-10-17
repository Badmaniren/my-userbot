import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.patch_pipeline_supervisor import PatchPipelineSupervisor, PatchPipelineSupervisorError
from skills.patch_analyzer import PatchAnalyzer
from skills.patch_verifier import PatchVerifier


class TestPatchPipelineSupervisorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        self.target_filename = f"test_file_{uuid.uuid4().hex[:8]}.py"
        self.target_file_path = os.path.join(self.repo_path, self.target_filename)

        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write("print('initial state')\n")

        self.supervisor = PatchPipelineSupervisor(repo_path=self.repo_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_process_patch_integration_flow(self):
        session_id = str(uuid.uuid4())
        random_code_marker = f"marker_{random.randint(10000, 99999)}"

        diff_text = f"""--- a/{self.target_filename}
+++ b/{self.target_filename}
@@ -1,1 +1,2 @@
 print('initial state')
+print('{random_code_marker}')
"""

        patch_data = {
            "id": session_id,
            "diff": diff_text,
            "target": self.target_filename
        }

        result = self.supervisor.process_patch(
            diff_text=diff_text,
            session_id=session_id,
            target_file=self.target_filename
        )

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("analyzed"))
        self.assertTrue(result.get("verified"))
        self.assertEqual(result.get("session_id"), session_id)
        self.assertIn("statistics", result)

        pipeline_result = self.supervisor.run_pipeline(patch_data)
        self.assertTrue(pipeline_result)

    def test_run_stream_pipeline_integration(self):
        session_id = str(uuid.uuid4())
        random_code_marker = f"stream_marker_{random.randint(10000, 99999)}"

        diff_text = f"""--- a/{self.target_filename}
+++ b/{self.target_filename}
@@ -1,1 +1,2 @@
 print('initial state')
+print('{random_code_marker}')
"""

        patch_data = {
            "id": session_id,
            "diff": diff_text,
            "target": self.target_filename
        }

        stream = iter([diff_text])

        stream_result = self.supervisor.run_stream_pipeline(stream, patch_data)
        self.assertTrue(stream_result)

    def test_pipeline_supervisor_error_wrapping(self):
        invalid_diff = "totally invalid malformed diff text without headers"
        session_id = str(uuid.uuid4())

        patch_data = {
            "id": session_id,
            "diff": invalid_diff,
            "target": self.target_filename
        }

        with self.assertRaises(PatchPipelineSupervisorError):
            self.supervisor.run_pipeline(patch_data)


if __name__ == "__main__":
    unittest.main()