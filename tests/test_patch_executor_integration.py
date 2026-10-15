import unittest
import os
import shutil
import uuid
import random
from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser
from skills.patch_executor import PatchExecutor, PatchExecutorError


class TestPatchExecutorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.abspath(f"test_repo_{uuid.uuid4().hex}")
        os.makedirs(self.test_dir, exist_ok=True)
        
        self.repo_path = self.test_dir
        self.git_inspector = GitInspector(repo_path=self.repo_path)
        self.lesson_parser = LessonParser(git_inspector=self.git_inspector)
        self.patch_executor = PatchExecutor(repo_path=self.repo_path, git_inspector=self.git_inspector, lesson_parser=self.lesson_parser)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_apply_patch_real_filesystem_and_execution(self):
        rand_file_name = f"file_{uuid.uuid4().hex}.py"
        rand_content = f"# Code content {uuid.uuid4().hex}"
        
        patch_data = {
            "file_path": rand_file_name,
            "content": rand_content
        }

        result = self.patch_executor.apply_patch(patch_data)
        self.assertTrue(result)

        full_file_path = os.path.join(self.repo_path, rand_file_name)
        self.assertTrue(os.path.exists(full_file_path))

        with open(full_file_path, "r", encoding="utf-8") as f:
            read_content = f.read()
        
        self.assertEqual(read_content, rand_content)

    def test_patch_executor_error_handling(self):
        invalid_patch_data = {
            "wrong_key": f"value_{uuid.uuid4().hex}"
        }

        with self.assertRaises(PatchExecutorError):
            self.patch_executor.apply_patch(invalid_patch_data)

    def test_execute_from_lessons_integration(self):
        rand_lesson_id = f"lesson_{uuid.randint(1000, 9999)}"
        rand_file = f"module_{uuid.uuid4().hex}.py"
        rand_text = f"print('{uuid.uuid4().hex}')"

        class DummyLessonParser:
            def __init__(self, l_id, f_path, content):
                self.l_id = l_id
                self.f_path = f_path
                self.content = content

            def parse_lessons(self):
                return [{
                    "id": self.l_id,
                    "patches": [{
                        "file_path": self.f_path,
                        "content": self.content
                    }]
                }]

        dummy_parser = DummyLessonParser(rand_lesson_id, rand_file, rand_text)
        self.patch_executor.lesson_parser = dummy_parser

        results = self.patch_executor.execute_from_lessons()

        self.assertIn(rand_lesson_id, results)
        self.assertTrue(results[rand_lesson_id])

        target_file = os.path.join(self.repo_path, rand_file)
        self.assertTrue(os.path.exists(target_file))
        with open(target_file, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), rand_text)


if __name__ == "__main__":
    unittest.main()