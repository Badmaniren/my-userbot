import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.patch_runner import PatchRunner, PatchRunnerError
from skills.patch_autocorrector import PatchAutocorrector
from skills.patch_executor import PatchExecutor


class TestPatchRunnerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        self.patch_runner = PatchRunner(repo_path=self.repo_path)

        self.unique_file_name = f"test_file_{uuid.uuid4().hex[:8]}.py"
        self.file_path = os.path.join(self.repo_path, self.unique_file_name)

        self.random_var_name = f"var_{uuid.uuid4().hex[:6]}"
        self.random_value = random.randint(1000, 9999)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_run_patch_integration_success(self):
        malformed_code = f"{self.random_var_name} = {self.random_value}\n# unclosed comment"

        patch_data = {
            "file_path": self.unique_file_name,
            "code": malformed_code
        }

        result = self.patch_runner.run_patch(patch_data)

        self.assertTrue(result, "Патч должен успешно выполниться через реальный автокорректор и исполнитель")

        self.assertTrue(os.path.exists(self.file_path), "Файл должен быть создан в репозитории")

        with open(self.file_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(self.random_var_name, content, "Содержимое патча должно присутствовать в созданном файле")

    def test_run_patch_integration_error_handling(self):
        invalid_patch_data = {
            "file_path": "",
            "code": ""
        }

        with self.assertRaises(PatchRunnerError):
            self.patch_runner.run_patch(invalid_patch_data)

    def test_process_stream_integration(self):
        stream_data = f"def {self.random_var_name}():\n    return {self.random_value}\n"

        transformed = self.patch_runner.process_stream(stream_data)

        self.assertIsInstance(transformed, str)
        self.assertIn(self.random_var_name, transformed)


if __name__ == "__main__":
    unittest.main()