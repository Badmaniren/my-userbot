import unittest
import os
import shutil
import uuid
import random
from skills.patch_executor import PatchExecutor, PatchExecutorError
from skills.lesson_parser import LessonParser
from skills.git_inspector import GitInspector


class TestPatchExecutorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.abspath(f"test_repo_{uuid.uuid4().hex}")
        os.makedirs(self.test_dir, exist_ok=True)
        
        git_dir = os.path.join(self.test_dir, ".git")
        os.makedirs(git_dir, exist_ok=True)

        self.git_inspector = GitInspector(repo_path=self.test_dir)
        self.lesson_parser = LessonParser(git_inspector=self.git_inspector)
        self.patch_executor = PatchExecutor(
            repo_path=self.test_dir,
            git_inspector=self.git_inspector,
            lesson_parser=self.lesson_parser
        )

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_integration_apply_and_execute_real_patch(self):
        random_file_name = f"module_{uuid.uuid4().hex[:8]}.py"
        random_content = f"# Generated content {uuid.uuid4()}"
        random_hyp_id = f"hyp_{random.randint(1000, 9999)}"

        patch_data = {
            "file_path": random_file_name,
            "content": random_content
        }

        success = self.patch_executor.apply_patch(patch_data)
        self.assertTrue(success)

        full_path = os.path.join(self.test_dir, random_file_name)
        self.assertTrue(os.path.exists(full_path))

        with open(full_path, "r", encoding="utf-8") as f:
            written_content = f.read()
        self.assertEqual(written_content, random_content)

        invalid_patch = {
            "invalid_key": uuid.uuid4().hex
        }
        with self.assertRaises(PatchExecutorError):
            self.patch_executor.apply_patch(invalid_patch)

    def test_integration_execute_from_lessons_no_suppression(self):
        results = self.patch_executor.execute_from_lessons()
        self.assertIsInstance(results, dict)
        
        patch_executor_unbound = PatchExecutor(repo_path=self.test_dir, lesson_parser=None)
        self.assertEqual(patch_executor_unbound.execute_from_lessons(), {})