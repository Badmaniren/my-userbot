import unittest
import tempfile
import os
import subprocess
import uuid
import random

from skills.patch_verifier import GitInspector, LessonParser, PatchExecutor, PatchVerifier

class TestPatchVerifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        
        subprocess.run(["git", "init", self.repo_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Test Bot"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "bot@test.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        self.init_file = os.path.join(self.repo_path, "README.md")
        with open(self.init_file, "w", encoding="utf-8") as f:
            f.write("Initial commit")
            
        subprocess.run(["git", "-C", self.repo_path, "add", "README.md"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.inspector = GitInspector(self.repo_path)
        self.parser = LessonParser(self.inspector)
        self.executor = PatchExecutor(self.repo_path, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.repo_path, self.inspector, self.executor)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_verify_and_apply_integration_success(self):
        unique_file_name = f"module_{uuid.uuid4().hex[:8]}.py"
        unique_content = f"# Random content {random.randint(1000, 9999)}\nprint('{uuid.uuid4()}')"
        unique_message = f"Add feature {uuid.uuid4().hex[:6]}"

        patch_data = {
            "file_path": unique_file_name,
            "content": unique_content,
            "commit_message": unique_message
        }

        result = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(result, "Интеграционная верификация и применение патча должны завершиться успехом")

        full_target_path = os.path.join(self.repo_path, unique_file_name)
        self.assertTrue(os.path.exists(full_target_path), "Целевой файл должен реально появиться в репозитории")

        with open(full_target_path, "r", encoding="utf-8") as f:
            written_content = f.read()
        self.assertEqual(written_content, unique_content, "Содержимое файла должно полностью совпадать с переданным в патче")

        history = self.inspector.get_commit_history(max_count=5)
        self.assertGreaterEqual(len(history), 2, "История коммитов должна содержать исходный и новый коммиты")
        self.assertEqual(history[0]["message"], unique_message, "Сообщение последнего коммита должно соответствовать переданному")

    def test_verify_and_apply_integration_failure_syntax(self):
        unique_file_name = f"broken_{uuid.uuid4().hex[:8]}.py"
        unique_content = f"syntax error here {random.randint(1, 100)}"
        
        patch_data = {
            "file_path": unique_file_name,
            "content": unique_content,
            "commit_message": "Should fail"
        }

        result = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(result, "Патч с маркером синтаксической ошибки должен быть отклонен верификатором")

        full_target_path = os.path.join(self.repo_path, unique_file_name)
        self.assertFalse(os.path.exists(full_target_path), "Файл с ошибкой не должен быть зафиксирован в репозитории")