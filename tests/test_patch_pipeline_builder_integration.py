import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.patch_pipeline_builder import PatchPipelineBuilder

class TestPatchPipelineBuilderIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        self.target_file_name = f"module_{uuid.uuid4().hex[:8]}.py"
        self.target_file_path = os.path.join(self.repo_path, self.target_file_name)

        self.random_string = uuid.uuid4().hex
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(f"# Initial code {self.random_string}\ndef existing_func():\n    return '{self.random_string}'\n")

        git_dir = os.path.join(self.repo_path, ".git")
        os.makedirs(git_dir, exist_ok=True)
        with open(os.path.join(git_dir, "config"), "w", encoding="utf-8") as f:
            f.write("[core]\n\trepositoryformatversion = 0\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_pipeline_builder_integration(self):
        pipeline = PatchPipelineBuilder(repo_path=self.repo_path)

        patch_uid = uuid.uuid4().hex
        patch_content = f"""
# Patch UID: {patch_uid}
def new_feature_{patch_uid}():
    return "{uuid.uuid4().hex}"
"""

        result = pipeline.run_pipeline(
            patch_content=patch_content,
            target_file=self.target_file_name
        )

        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, "is_safe"))
        self.assertTrue(hasattr(result, "is_valid"))

        with open(self.target_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(patch_uid, content)

if __name__ == "__main__":
    unittest.main()