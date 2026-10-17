import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.patch_pipeline_controller import PatchPipelineController
from skills.patch_evaluator import PatchEvaluator
from skills.patch_verifier import PatchVerifier


class TestPatchPipelineControllerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        self.unique_file_name = f"target_{uuid.uuid4().hex}.py"
        self.target_file_path = os.path.join(self.repo_path, self.unique_file_name)
        
        self.initial_code = f"# Initial code {uuid.uuid4()}\nprint('hello')\n"
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(self.initial_code)

        os.system(f"git -C {self.repo_path} init")
        os.system(f"git -C {self.repo_path} config user.name 'Test Architect'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com'")
        os.system(f"git -C {self.repo_path} add {self.unique_file_name}")
        os.system(f"git -C {self.repo_path} commit -m 'Initial commit {uuid.uuid4()}'")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_pipeline_controller_integration_flow(self):
        random_str = uuid.uuid4().hex
        patch_content = f"# Patch content {random_str}\nprint('{random_str}')\n"

        controller = PatchPipelineController(repo_path=self.repo_path)

        result = controller.run_pipeline(
            patch_content=patch_content,
            target_file=self.unique_file_name
        )

        self.assertIsNotNone(result)
        
        with open(self.target_file_path, "r", encoding="utf-8") as f:
            file_content = f.read()

        self.assertIn(random_str, file_content)


if __name__ == "__main__":
    unittest.main()