import unittest
import uuid
import random
import os
import tempfile
from skills.patch_validator import PatchValidator, PatchValidatorError
from skills.code_validator import CodeValidator
from skills.patch_sanitizer import PatchSanitizer
from skills.git_inspector import GitInspector


class TestPatchValidatorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name

        # Инициализация реального git репозитория для интеграционного теста
        os.system(f"git -C {self.repo_path} init -b main")
        os.system(f"git -C {self.repo_path} config user.name 'Test Architect'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com'")

        # Создаем начальный файл для тестов диффов
        self.target_file_name = f"file_{uuid.uuid4().hex[:8]}.py"
        self.target_file_path = os.path.join(self.repo_path, self.target_file_name)

        self.initial_content = f"# Initial file {uuid.uuid4()}\n\ndef compute():\n    return 42\n"
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)

        os.system(f"git -C {self.repo_path} add {self.target_file_name}")
        os.system(f"git -C {self.repo_path} commit -m 'Initial commit'")

        # Инициализация реальных зависимостей без моков
        self.code_validator = CodeValidator() if 'CodeValidator' in globals() else None
        self.patch_sanitizer = PatchSanitizer()
        self.git_inspector = GitInspector(repo_path=self.repo_path)

        self.validator = PatchValidator(
            repo_path=self.repo_path,
            code_validator=self.code_validator,
            patch_sanitizer=self.patch_sanitizer,
            git_inspector=self.git_inspector
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_full_patch_validation_and_application_integration(self):
        rand_val = random.randint(100, 999)
        unique_func_name = f"func_{uuid.uuid4().hex[:6]}"

        # Формируем валидный патч (diff) для реального применения в репозитории
        diff_content = f"""diff --git a/{self.target_file_name} b/{self.target_file_name}
index 1111111..2222222 100644
--- a/{self.target_file_name}
+++ b/{self.target_file_name}
@@ -2,3 +2,6 @@

 def compute():
     return 42
+
+def {unique_func_name}():
+    return {rand_val}
"""

        # Проверка чтения потока патча
        patch_file_path = os.path.join(self.repo_path, f"patch_{uuid.uuid4().hex[:6]}.diff")
        with open(patch_file_path, "w", encoding="utf-8") as f:
            f.write(diff_content)

        read_content = self.validator.read_patch_stream(patch_file_path)
        self.assertIn(unique_func_name, read_content)

        # Полный интеграционный цикл валидации и применения патча
        validation_result = self.validator.validate_patch(read_content)
        self.assertTrue(validation_result.is_valid)

        applied = self.validator.apply_and_test_diff(read_content)
        self.assertTrue(applied)

        # Проверяем, что файл действительно изменился в реальной файловой системе репозитория
        with open(self.target_file_path, "r", encoding="utf-8") as f:
            updated_code = f.read()

        self.assertIn(unique_func_name, updated_code)
        self.assertIn(str(rand_val), updated_code)

        # Проверка безопасности синтаксиса через AST
        safe_code = f"x = {rand_val}\nprint(x)"
        self.assertTrue(self.validator.validate_syntax(safe_code))
        self.assertTrue(self.validator.perform_security_check(safe_code))

        # Проверка детектирования опасных импортов
        dangerous_code = "import os\nos.system('echo hacked')"
        with self.assertRaises(PatchValidatorError):
            self.validator.perform_security_check(dangerous_code)


if __name__ == "__main__":
    unittest.main()