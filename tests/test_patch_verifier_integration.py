import unittest
import os
import tempfile
import uuid
import random
import subprocess
from skills.patch_verifier import GitInspector, LessonParser, PatchExecutor, PatchVerifier

class TestPatchVerifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        
        subprocess.run(["git", "init", self.repo_path], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Test User"], check=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "test@example.com"], check=True)
        
        initial_file = os.path.join(self.repo_path, "README.md")
        with open(initial_file, "w", encoding="utf-8") as f:
            f.write("Initial commit")
            
        subprocess.run(["git", "-C", self.repo_path, "add", "README.md"], check=True)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", "Initial commit"], check=True)

        self.inspector = GitInspector(self.repo_path)
        self.parser = LessonParser(self.inspector)
        self.executor = PatchExecutor(self.repo_path, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.repo_path, self.inspector, self.executor)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_verify_and_apply_success_integration(self):
        rand_filename = f"module_{uuid.uuid4().hex[:8]}.py"
        rand_content = f"# Valid content {uuid.uuid4()}"
        rand_commit_msg = f"Add {rand_filename} with id {random.randint(1000, 9999)}"

        patch_data = {
            "file_path": rand_filename,
            "content": rand_content,
            "commit_message": rand_commit_msg
        }

        success = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(success, "Верификатор должен успешно одобрить и применить корректный патч.")

        target_file_path = os.path.join(self.repo_path, rand_filename)
        self.assertTrue(os.path.exists(target_file_path), "Файл патча должен реально появиться в репозитории.")

        with open(target_file_path, "r", encoding="utf-8") as f:
            written_content = f.read()
        self.assertEqual(written_content, rand_content, "Содержимое файла должно точно совпадать с переданным в патче.")

        history = self.inspector.get_commit_history(max_count=1)
        self.assertTrue(len(history) > 0, "История коммитов должна содержать новый коммит.")
        latest_commit = history[0]
        self.assertEqual(latest_commit["message"], rand_commit_msg, "Сообщение коммита должно соответствовать заданному.")

    def test_verify_and_apply_syntax_error_integration(self):
        rand_filename = f"broken_{uuid.uuid4().hex[:8]}.py"
        rand_content = f"print('syntax error here') # {uuid.uuid4()}"

        patch_data = {
            "file_path": rand_filename,
            "content": rand_content,
            "commit_message": "Should fail"
        }

        success = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(success, "Верификатор должен отклонить патч, содержащий синтаксическую ошибку.")

        target_file_path = os.path.join(self.repo_path, rand_filename)
        self.assertFalse(os.path.exists(target_file_path), "Файл с ошибкой не должен быть записан в репозиторий через экзекутор.")

if __name__ == "__main__":
    unittest.main()