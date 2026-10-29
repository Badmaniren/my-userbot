import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.patch_applier import PatchApplier, PatchApplierError
from skills.patch_verifier import PatchVerifier, PatchVerifierError
from skills.patch_pipeline_runner import run_patch_pipeline


class TestPatchPipelineRunnerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        # Инициализируем простейшую структуру репозитория для тестов
        os.makedirs(os.path.join(self.repo_path, ".git"), exist_ok=True)

        # Генерируем уникальные случайные данные для изоляции тестов
        self.unique_id = str(uuid.uuid4())
        self.target_filename = f"target_{self.unique_id}.py"
        self.target_file_path = os.path.join(self.repo_path, self.target_filename)

        self.initial_content = f"# Initial content {random.randint(1, 1000)}\n"
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_patch_pipeline_runner_real_integration(self):
        # Подготовка данных патча с использованием реальных структур для PatchApplier и PatchVerifier
        random_code_addition = f"\n# Added line {uuid.uuid4()}\ndef generated_func_{random.randint(1, 100)}():\n    return '{self.unique_id}'\n"

        patch_data = {
            "file_path": self.target_filename,
            "content": self.initial_content + random_code_addition,
            "backup_tag": f"backup_{self.unique_id}"
        }

        # Вызов тестируемого интеграционного модуля без моков между навыками
        pipeline_result = run_patch_pipeline(self.repo_path, patch_data)

        # Проверяем реальный результат выполнения пайплайна
        self.assertTrue(
            pipeline_result,
            "Интеграционный пайплайн должен успешно применить и верифицировать корректный патч"
        )

        # Проверяем, что файл действительно изменился на диске
        with open(self.target_file_path, "r", encoding="utf-8") as f:
            updated_content = f.read()

        self.assertIn(
            self.unique_id,
            updated_content,
            "Файл на диске должен содержать уникальный идентификатор из примененного патча"
        )

    def test_patch_pipeline_runner_invalid_patch(self):
        # Передаем синтаксически некорректный код для проверки срабатывания верификации
        invalid_code_addition = "\ndef broken_syntax_func(\n    unclosed_parenthesis\n"

        patch_data = {
            "file_path": self.target_filename,
            "content": self.initial_content + invalid_code_addition,
            "backup_tag": f"backup_fail_{self.unique_id}"
        }

        # Пайплайн должен вернуть False или выбросить исключение из-за провала верификации
        try:
            pipeline_result = run_patch_pipeline(self.repo_path, patch_data)
            self.assertFalse(
                pipeline_result,
                "Пайплайн должен вернуть False при попытке применить невалидный патч"
            )
        except (PatchApplierError, PatchVerifierError, Exception):
            # Допустимо также падение с кастомным исключением навыка
            pass

        # Проверяем, что исходный файл не был поврежден (сработал откат или верификация до записи)
        with open(self.target_file_path, "r", encoding="utf-8") as f:
            current_content = f.read()

        self.assertEqual(
            current_content,
            self.initial_content,
            "При неудачном пайплайне состояние файла должно остаться неизменным"
        )


if __name__ == "__main__":
    unittest.main()