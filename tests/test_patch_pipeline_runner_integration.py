import unittest
import uuid
import random
import tempfile
import shutil
import os

from skills.code_validator import CodeValidator
from skills.patch_autocorrector import PatchAutocorrector
from skills.patch_pipeline_runner import PatchPipelineRunner


class TestPatchPipelineRunnerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        self.validator = CodeValidator(repo_path=self.repo_path)
        self.autocorrector = PatchAutocorrector(repo_path=self.repo_path, sanitizer=None, validator=self.validator)

        self.pipeline = PatchPipelineRunner(
            repo_path=self.repo_path,
            validator=self.validator,
            autocorrector=self.autocorrector
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_pipeline_integration_flow(self):
        unique_id = uuid.uuid4().hex
        random_value = random.randint(1000, 9999)

        file_name = f"module_{unique_id}.py"
        malformed_code = f"""
def compute_{unique_id}():
    x = {random_value}
    # malformed syntax without proper closing or containing anti-pattern if any
    return x
"""

        result = self.pipeline.run_pipeline(file_name=file_name, code_fragment=malformed_code)

        self.assertTrue(
            result,
            f"Интеграционный конвейер должен успешно обработать и применить валидный фрагмент для ID {unique_id}"
        )

        full_file_path = os.path.join(self.repo_path, file_name)
        self.assertTrue(
            os.path.exists(full_file_path),
            f"Файл {file_name} должен быть физически создан в репозитории."
        )

        with open(full_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn(
            str(random_value),
            content,
            f"Сгенерированное случайное значение {random_value} должно присутствовать в конечном файле."
        )
        self.assertIn(
            unique_id,
            content,
            f"Уникальный идентификатор {unique_id} должен присутствовать в конечном коде."
        )


if __name__ == "__main__":
    unittest.main()