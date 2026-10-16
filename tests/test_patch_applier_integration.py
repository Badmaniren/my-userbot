import unittest
import os
import uuid
import shutil
import tempfile
from skills.patch_applier import PatchApplier
from skills.patch_autocorrector import PatchAutocorrector
from skills.patch_executor import PatchExecutor
from skills.git_inspector import GitInspector

class TestPatchApplierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.test_dir, "repo")
        os.makedirs(self.repo_path)

        # Инициализация зависимостей
        self.git_inspector = GitInspector(self.repo_path)
        self.autocorrector = PatchAutocorrector(self.repo_path, None, None)
        self.executor = PatchExecutor(self.repo_path, self.git_inspector, None)

        # Инициализация тестируемого модуля
        self.applier = PatchApplier(self.autocorrector, self.executor)

        self.file_name = f"test_file_{uuid.uuid4().hex}.py"
        self.file_path = os.path.join(self.repo_path, self.file_name)
        with open(self.file_path, "w") as f:
            f.write("def hello():\n    print('world')")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_full_patch_lifecycle_integration(self):
        # Генерируем случайные данные для патча
        patch_id = str(uuid.uuid4())
        malformed_code = "def hello():\n print('world') \n  # Indentation error here"

        # 1. Проверка коррекции через PatchAutocorrector (внутри PatchApplier)
        # 2. Проверка исполнения через PatchExecutor (внутри PatchApplier)

        patch_data = {
            "id": patch_id,
            "file_name": self.file_name,
            "content": malformed_code
        }

        # Вызов тестируемого модуля
        result = self.applier.apply_and_verify(patch_data)

        # Проверка результата
        self.assertTrue(result, "Патч должен быть успешно применен после коррекции")

        # Проверка реальных изменений в файловой системе
        with open(self.file_path, "r") as f:
            content = f.read()
            self.assertIn("print('world')", content)
            self.assertNotIn("Indentation error", content)

    def test_invalid_patch_rejection(self):
        # Генерируем заведомо неисправимый код
        bad_patch = {
            "id": str(uuid.uuid4()),
            "file_name": self.file_name,
            "content": "!!! INVALID SYNTAX @@@"
        }

        # Проверяем, что система корректно обрабатывает отказ
        with self.assertRaises(Exception):
            self.applier.apply_and_verify(bad_patch)

if __name__ == '__main__':
    unittest.main()