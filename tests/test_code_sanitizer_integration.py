import unittest
import uuid
import random
import tempfile
import os
import shutil

from skills.code_sanitizer import CodeSanitizer
from skills.patch_executor import PatchExecutor
from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser


class TestCodeSanitizerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        # Инициализируем реальные связанные модули без моков
        self.git_inspector = GitInspector(self.repo_path)
        self.lesson_parser = LessonParser(self.git_inspector)
        self.patch_executor = PatchExecutor(
            repo_path=self.repo_path,
            git_inspector=self.git_inspector,
            lesson_parser=self.lesson_parser
        )
        self.sanitizer = CodeSanitizer()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_code_sanitizer_integration_flow(self):
        # Генерируем случайные данные для теста, исключая хардкод
        random_id = uuid.uuid4().hex[:8]
        target_filename = f"module_{random_id}.py"
        target_path = os.path.join(self.repo_path, target_filename)
        
        # Создаем патч, содержащий запрещенный антипаттерн (except Exception: pass)
        # Код санитизатор должен обнаружить и очистить его перед передачей в исполнитель
        dirty_code = (
            f"def compute_{random_id}():\n"
            f"    try:\n"
            f"        raise ValueError('Random error {random_id}')\n"
            f"    except Exception:\n"
            f"        pass\n"
            f"    return '{random_id}'\n"
        )
        
        patch_data = {
            "file_path": target_filename,
            "content": dirty_code
        }

        # Шаг 1: Проверяем синтаксис и очищаем патч через CodeSanitizer
        sanitized_content = self.sanitizer.sanitize_patch(patch_data["content"])
        
        # Убедимся, что антипаттерн был модифицирован/удален санитизатором
        self.assertNotIn("except Exception:\n        pass", sanitized_content)
        
        # Шаг 2: Передаем очищенный патч в реальный PatchExecutor
        clean_patch_data = {
            "file_path": target_filename,
            "content": sanitized_content
        }
        
        execution_success = self.patch_executor.apply_patch(clean_patch_data)
        self.assertTrue(execution_success, "PatchExecutor должен успешно применить очищенный патч")

        # Шаг 3: Проверяем реальные изменения в файловой системе
        self.assertTrue(os.path.exists(target_path), "Файл должен быть создан на диске")
        
        with open(target_path, "r", encoding="utf-8") as f:
            file_contents = f.read()
            
        # Проверяем, что уникальный идентификатор присутствует в записанном файле
        self.assertIn(random_id, file_contents)

        # Шаг 4: Проверяем интеграцию через GitInspector
        latest_changes = self.git_inspector.get_latest_changes()
        self.assertIsInstance(latest_changes, (str, dict, list))


if __name__ == "__main__":
    unittest.main()