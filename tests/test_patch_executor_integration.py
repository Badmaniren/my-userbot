import unittest
import os
import shutil
import tempfile
import uuid
import random

from skills.patch_executor import PatchExecutor, PatchExecutorError
from skills.lesson_parser import LessonParser
from skills.git_inspector import GitInspector


class IntegrationTestPatchExecutor(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix=f"patch_exec_test_{uuid.uuid4().hex}_")
        self.repo_path = self.test_dir
        
        self.git_inspector = GitInspector(repo_path=self.repo_path)
        self.lesson_parser = LessonParser(git_inspector=self.git_inspector)
        self.patch_executor = PatchExecutor(
            repo_path=self.repo_path,
            git_inspector=self.git_inspector,
            lesson_parser=self.lesson_parser
        )

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_patch_application_and_atomic_validation_integration(self):
        random_suffix = uuid.uuid4().hex[:8]
        target_file = f"module_{random_suffix}.py"
        random_content = f"# Generated content {random.randint(1000, 9999)}"

        patch_data = {
            "file_path": target_file,
            "content": random_content
        }

        success = self.patch_executor.apply_patch(patch_data)
        self.assertTrue(success)

        full_path = os.path.join(self.repo_path, target_file)
        self.assertTrue(os.path.exists(full_path))

        with open(full_path, "r", encoding="utf-8") as f:
            content_on_disk = f.read()

        self.assertEqual(content_on_disk, random_content)

    def test_invalid_patch_data_raises_error(self):
        invalid_patch = {
            "invalid_key": f"data_{uuid.uuid4().hex}"
        }

        with self.assertRaises(PatchExecutorError):
            self.patch_executor.apply_patch(invalid_patch)


if __name__ == "__main__":
    unittest.main()