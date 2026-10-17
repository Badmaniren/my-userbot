import unittest
import os
import tempfile
import shutil
import uuid
import subprocess

from skills.git_inspector import GitInspector
from skills.patch_evaluator import PatchEvaluator
from skills.patch_verifier import PatchVerifier
from skills.patch_executor import PatchExecutor

class TestPatchVerifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "-C", self.test_dir, "init"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Test User"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "test@example.com"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        self.initial_file = "init_file.py"
        self.initial_path = os.path.join(self.test_dir, self.initial_file)
        with open(self.initial_path, "w", encoding="utf-8") as f:
            f.write("# Initial commit\n")

        subprocess.run(["git", "-C", self.test_dir, "add", self.initial_file], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", "Initial commit"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_patch_verifier_integration_workflow(self):
        unique_filename = f"module_{uuid.uuid4().hex[:8]}.py"
        unique_content = f"# Unique content UUID: {uuid.uuid4()}\nx = 42\n"
        unique_message = f"Add feature {uuid.uuid4().hex[:6]}"

        inspector = GitInspector(self.test_dir)
        evaluator = PatchEvaluator(self.test_dir)
        executor = PatchExecutor(self.test_dir, inspector, None)

        verifier = PatchVerifier(self.test_dir, inspector, executor)

        patch_data = {
            "file_path": unique_filename,
            "content": unique_content,
            "commit_message": unique_message
        }

        eval_result = evaluator.evaluate(unique_content, target_file=unique_filename)
        self.assertIsNotNone(eval_result)

        success = verifier.verify_and_apply(patch_data)
        self.assertTrue(success, "PatchVerifier должен успешно верифицировать и применить валидный патч")

        target_full_path = os.path.join(self.test_dir, unique_filename)
        self.assertTrue(os.path.exists(target_full_path), "Файл из патча должен физически появиться в репозитории")

        with open(target_full_path, "r", encoding="utf-8") as f:
            written_content = f.read()
        self.assertEqual(written_content, unique_content, "Содержимое файла должно совпадать с переданным в патче")

        repo_analysis = inspector.analyze_repository()
        self.assertGreaterEqual(repo_analysis["total_commits"], 2, "Количество коммитов должно увеличиться после применения патча")

        latest_commit = repo_analysis["latest_commit"]
        self.assertEqual(latest_commit["message"], unique_message, "Сообщение последнего коммита должно соответствовать переданному")

        history = inspector.get_commit_history(max_count=5)
        found_commit = any(h["message"] == unique_message for h in history)
        self.assertTrue(found_commit, "История коммитов через GitInspector должна содержать новый коммит")

    def test_patch_verifier_rejects_invalid_patch(self):
        unique_filename = f"bad_module_{uuid.uuid4().hex[:8]}.py"
        unique_content = "syntax error here\n"

        inspector = GitInspector(self.test_dir)
        executor = PatchExecutor(self.test_dir, inspector, None)
        verifier = PatchVerifier(self.test_dir, inspector, executor)

        patch_data = {
            "file_path": unique_filename,
            "content": unique_content,
            "commit_message": "Bad patch"
        }

        success = verifier.verify_and_apply(patch_data)
        self.assertFalse(success, "PatchVerifier должен отклонить патч с синтаксической ошибкой")

        target_full_path = os.path.join(self.test_dir, unique_filename)
        self.assertFalse(os.path.exists(target_full_path), "Файл отклоненного патча не должен создаваться в репозитории")

if __name__ == "__main__":
    unittest.main()