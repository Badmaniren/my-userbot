import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.patch_runner import PatchRunner
from skills.code_validator import CodeValidator
from skills.patch_autocorrector import PatchAutocorrector
from skills.patch_executor import PatchExecutor
from skills.code_sanitizer import CodeSanitizer


class TestPatchRunnerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        self.sanitizer = CodeSanitizer() if 'CodeSanitizer' in globals() else None
        self.validator = CodeValidator(repo_path=self.repo_path)
        self.autocorrector = PatchAutocorrector(
            repo_path=self.repo_path,
            sanitizer=self.sanitizer,
            validator=self.validator
        )
        self.executor = PatchExecutor(
            repo_path=self.repo_path,
            git_inspector=None,
            lesson_parser=None
        )

        self.patch_runner = PatchRunner(
            validator=self.validator,
            autocorrector=self.autocorrector,
            executor=self.executor
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_end_to_end_patch_pipeline_integration(self):
        unique_id = str(uuid.uuid4())
        file_name = f"target_{unique_id}.py"
        random_value = random.randint(1000, 9999)

        func_name = f"compute_{unique_id.replace('-', '_')}"
        malformed_code = f"def {func_name}():\n    print({random_value})\n    return {random_value}"

        patch_payload = {
            "file_path": file_name,
            "content": malformed_code
        }

        result = self.patch_runner.run_pipeline(patch_payload)

        self.assertTrue(result, "Конвейер обязан успешно обработать и применить валидный патч.")

        target_file_path = os.path.join(self.repo_path, file_name)
        self.assertTrue(os.path.exists(target_file_path), "Файл патча должен реально появиться в репозитории.")

        with open(target_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(str(random_value), content, "Содержимое файла должно соответствовать переданному случайному значению.")


if __name__ == "__main__":
    unittest.main()