import unittest
import uuid
import random
import os
import shutil
from skills.patch_pipeline import PatchPipeline
from skills.code_sanitizer import CodeSanitizer
from skills.code_validator import CodeValidator
from skills.patch_autocorrector import PatchAutocorrector

class TestPatchPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/test_repo_{uuid.uuid4().hex}"
        os.makedirs(self.repo_path, exist_ok=True)

        self.sanitizer = CodeSanitizer(repo_path=self.repo_path)
        self.validator = CodeValidator(repo_path=self.repo_path)
        self.autocorrector = PatchAutocorrector(
            repo_path=self.repo_path,
            sanitizer=self.sanitizer,
            validator=self.validator
        )

        self.pipeline = PatchPipeline(
            sanitizer=self.sanitizer,
            validator=self.validator,
            autocorrector=self.autocorrector
        )

    def tearDown(self):
        if os.path.exists(self.repo_path):
            shutil.rmtree(self.repo_path)

    def test_full_pipeline_flow_with_random_data(self):
        # Генерируем случайный "плохой" код с антипаттерном
        random_id = uuid.uuid4().hex
        malformed_code = f"def test_func_{random_id}():\n    try:\n        pass\n    except Exception:\n        pass # Antipattern"

        # Добавляем правила для проверки
        self.sanitizer.add_forbidden_pattern("except Exception:")
        self.validator.add_forbidden_construct("except Exception:")

        # Выполняем пайплайн
        # Ожидаем, что пайплайн пройдет через санитизацию, валидацию и автокоррекцию
        processed_code = self.pipeline.process(malformed_code)

        # Проверки
        self.assertIsInstance(processed_code, str)
        self.assertNotIn("except Exception:", processed_code)

        # Проверяем, что код валиден после обработки
        is_valid = self.validator.validate_code(processed_code)
        self.assertTrue(is_valid, "Код должен быть валидным после прохождения пайплайна")

    def test_batch_processing_integrity(self):
        # Генерируем набор случайных фрагментов
        batch_size = random.randint(3, 7)
        patch_batch = {
            f"file_{uuid.uuid4().hex}.py": f"def func_{i}(): return {random.randint(1, 100)}"
            for i in range(batch_size)
        }

        results = self.pipeline.process_batch(patch_batch)

        self.assertEqual(len(results), batch_size)
        for file_name, code in results.items():
            self.assertTrue(self.validator.validate_code(code))
            self.assertIn("def func_", code)

    def test_pipeline_error_handling_on_invalid_input(self):
        # Попытка обработки кода, который невозможно исправить
        invalid_syntax = "def invalid_syntax( : " # Синтаксическая ошибка

        with self.assertRaises(Exception):
            self.pipeline.process(invalid_syntax)

if __name__ == '__main__':
    unittest.main()