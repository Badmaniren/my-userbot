import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.patch_verifier import PatchVerifier
from skills.patch_executor import PatchExecutor
from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser

class TestPatchVerifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        os.system(f"git -C {self.test_dir} init -b main")
        os.system(f"git -C {self.test_dir} config user.name 'Test Architect'")
        os.system(f"git -C {self.test_dir} config user.email 'architect@test.com'")

        self.git_inspector = GitInspector(self.test_dir)
        self.lesson_parser = LessonParser(self.git_inspector)
        self.patch_executor = PatchExecutor(self.test_dir, self.git_inspector, self.lesson_parser)
        self.patch_verifier = PatchVerifier()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_patch_verifier_integration_with_real_code(self):
        unique_id = str(uuid.uuid4())
        random_value = random.randint(1000, 9999)
        file_name = f"module_{unique_id}.py"
        file_path = os.path.join(self.test_dir, file_name)

        func_suffix = unique_id.replace("-", "_")
        valid_code = f"""
# Unique ID: {unique_id}
def compute_{func_suffix}():
    return {random_value}
"""
        patch_data = {
            "file_path": file_name,
            "content": valid_code
        }

        is_verified = self.patch_verifier.verify(patch_data)
        self.assertTrue(is_verified, "Verifier должен пропустить валидный синтаксис AST.")

        applied = self.patch_executor.apply_patch(patch_data)
        self.assertTrue(applied, "PatchExecutor должен успешно применить верифицированный патч.")

        self.assertTrue(os.path.exists(file_path), "Файл должен реально появиться на диске.")

        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(unique_id, content, "Содержимое файла должно содержать сгенерированный UUID.")
        self.assertIn(str(random_value), content, "Содержимое файла должно содержать сгенерированное случайное число.")

        invalid_code = f"""
def broken_syntax_{func_suffix}(
    print("Missing closing parenthesis"
"""
        invalid_patch_data = {
            "file_path": file_name,
            "content": invalid_code
        }

        is_invalid_verified = self.patch_verifier.verify(invalid_patch_data)
        self.assertFalse(is_invalid_verified, "Verifier должен заблокировать невалидный AST (синтаксическую ошибку).")