import unittest
import io
import os
import shutil
import uuid
import random
from skills.patch_pipeline import PatchPipeline, run_pipeline, PatchPipelineError

class TestPatchPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_id = str(uuid.uuid4())[:8]
        self.repo_path = f"./test_repo_{self.test_id}"
        os.makedirs(self.repo_path, exist_ok=True)

        self.target_file = f"file_{self.test_id}.txt"
        self.file_path = os.path.join(self.repo_path, self.target_file)

        self.initial_content = f"Line 1: {random.randint(1000, 9999)}\nLine 2: initial\n"
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)

    def tearDown(self):
        if os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path, ignore_errors=True)

    def test_pipeline_successful_integration(self):
        unique_marker = f"patch_applied_{random.randint(10000, 99999)}"
        line1_content = self.initial_content.splitlines()[0]
        patch_content = f"""--- {self.target_file}
+++ {self.target_file}
@@ -1,2 +1,3 @@
 {line1_content}
 Line 2: initial
+{unique_marker}
"""
        stream = io.BytesIO(patch_content.encode('utf-8'))
        policy = "strict"

        result = run_pipeline(stream, self.repo_path, self.target_file, policy)
        self.assertTrue(result)

        with open(self.file_path, "r", encoding="utf-8") as f:
            updated_content = f.read()

        self.assertIn(unique_marker, updated_content)

    def test_pipeline_error_handling_invalid_patch(self):
        invalid_patch = f"INVALID UNSTRUCTRED PATCH DATA {uuid.uuid4()}"

        with self.assertRaises(PatchPipelineError):
            run_pipeline(invalid_patch, self.repo_path, self.target_file, "strict")

if __name__ == "__main__":
    unittest.main()