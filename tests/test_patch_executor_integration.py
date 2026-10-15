import unittest
import os
import shutil
import uuid
import random
from skills.patch_executor import PatchExecutor, PatchExecutorError
from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser


class TestPatchExecutorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = f"test_repo_{uuid.uuid4().hex}"
        self.repo_path = os.path.abspath(self.test_dir)
        os.makedirs(self.repo_path, exist_ok=True)
        
        self.git_inspector = GitInspector(repo_path=self.repo_path)
        self.lesson_parser = LessonParser(git_inspector=self.git_inspector)
        self.patch_executor = PatchExecutor(
            repo_path=self.repo_path,
            git_inspector=self.git_inspector,
            lesson_parser=self.lesson_parser
        )

    def tearDown(self):
        if os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path)

    def test_integration_patch_application_and_rollback(self):
        random_file_name = f"module_{uuid.uuid4().hex[:8]}.py"
        random_content_v1 = f"# Version 1: {random.randint(1000, 9999)}"
        random_content_v2 = f"# Version 2: {random.randint(10000, 99999)}"

        patch_data = {
            "file_path": random_file_name,
            "content": random_content_v1
        }

        applied = self.patch_executor.apply_patch(patch_data)
        self.assertTrue(applied, "Патч должен успешно примениться")

        full_file_path = os.path.join(self.repo_path, random_file_name)
        self.assertTrue(os.path.exists(full_file_path), "Файл должен быть создан на диске")

        with open(full_file_path, "r", encoding="utf-8") as f:
            written_content = f.read()
        self.assertEqual(written_content, random_content_v1, "Содержимое файла должно совпадать с переданным в патче")

        os.system(f"git -C {self.repo_path} init")
        os.system(f"git -C {self.repo_path} config user.name 'Test Bot'")
        os.system(f"git -C {self.repo_path} config user.email 'bot@test.com'")
        os.system(f"git -C {self.repo_path} add {random_file_name}")
        os.system(f"git -C {self.repo_path} commit -m 'Initial commit'")

        commit_history = self.git_inspector.get_commit_history(max_count=1)
        self.assertTrue(len(commit_history) > 0, "История коммитов должна содержать хотя бы один коммит")
        initial_commit_hash = commit_history[0].get("hash") if isinstance(commit_history[0], dict) else getattr(commit_history[0], "hash", None)

        patch_data_v2 = {
            "file_path": random_file_name,
            "content": random_content_v2
        }
        self.patch_executor.apply_patch(patch_data_v2)

        with open(full_file_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), random_content_v2, "Файл должен обновиться до второй версии")

        if initial_commit_hash:
            rolled_back = self.patch_executor.rollback_patch(random_file_name, initial_commit_hash)
            self.assertTrue(rolled_back, "Откат патча должен завершиться успешно")

            with open(full_file_path, "r", encoding="utf-8") as f:
                rolled_content = f.read()
            self.assertEqual(rolled_content, random_content_v1, "Содержимое файла после отката должно соответствовать первому коммиту")


if __name__ == "__main__":
    unittest.main()