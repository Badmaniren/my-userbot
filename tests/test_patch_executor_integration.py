import unittest
import tempfile
import os
import shutil
import uuid
import random

from skills.patch_executor import PatchExecutor, PatchExecutorError
from skills.git_inspector import GitInspector


class DummyLessonParser:
    def __init__(self, hypotheses):
        self.hypotheses = hypotheses

    def parse_lessons(self):
        return self.hypotheses


class TestPatchExecutorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        # Инициализируем реальный Git-репозиторий для интеграции с GitInspector
        os.system(f"git -C {self.repo_path} init -b main")
        os.system(f"git -C {self.repo_path} config user.name 'Test User'")
        os.system(f"git -C {self.repo_path} config user.email 'test@example.com'")

        self.git_inspector = GitInspector(repo_path=self.repo_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_apply_patch_and_execute_from_lessons_integration(self):
        # Генерируем случайные данные для исключения хардкода
        unique_id = f"hyp_{uuid.uuid4().hex[:8]}"
        file_name = f"test_file_{random.randint(1000, 9999)}.py"
        file_content = f"# Generated content {uuid.uuid4()}"

        hypotheses = [
            {
                "id": unique_id,
                "patches": [
                    {
                        "file_path": file_name,
                        "content": file_content
                    }
                ]
            }
        ]

        lesson_parser = DummyLessonParser(hypotheses)
        executor = PatchExecutor(
            repo_path=self.repo_path,
            git_inspector=self.git_inspector,
            lesson_parser=lesson_parser
        )

        # Выполняем интеграционный метод из уроков
        results = executor.execute_from_lessons()

        # Проверяем возврат конкретных случайных ID и успешность выполнения
        self.assertIn(unique_id, results)
        self.assertTrue(results[unique_id])

        # Проверяем реальное появление файла на диске с правильным содержимым
        full_file_path = os.path.join(self.repo_path, file_name)
        self.assertTrue(os.path.exists(full_file_path))

        with open(full_file_path, "r", encoding="utf-8") as f:
            read_content = f.read()
        self.assertEqual(read_content, file_content)

    def test_rollback_patch_integration(self):
        # Создаем начальное состояние файла и фиксируем его в git
        file_name = f"rollback_file_{random.randint(1000, 9999)}.txt"
        initial_content = f"Initial state {uuid.uuid4()}"
        full_path = os.path.join(self.repo_path, file_name)

        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(initial_content)

        os.system(f"git -C {self.repo_path} add {file_name}")
        os.system(f"git -C {self.repo_path} commit -m 'Initial commit'")

        # Получаем реальный хэш коммита через GitInspector
        history = self.git_inspector.get_commit_history(max_count=1)
        commit_hash = history[0].get("hash") or history[0].get("commit") if isinstance(history[0], dict) else history[0]

        executor = PatchExecutor(
            repo_path=self.repo_path,
            git_inspector=self.git_inspector
        )

        # Применяем патч (перезаписываем файл новым случайным содержимым)
        new_content = f"Modified state {uuid.uuid4()}"
        patch_data = {
            "file_path": file_name,
            "content": new_content
        }
        executor.apply_patch(patch_data)

        with open(full_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), new_content)

        # Выполняем откат изменений к начальному коммиту
        rollback_success = executor.rollback_patch(file_name, commit_hash)
        self.assertTrue(rollback_success)

        # Проверяем, что файл вернулся к исходному состоянию
        with open(full_path, "r", encoding="utf-8") as f:
            restored_content = f.read()
        self.assertEqual(restored_content, initial_content)


if __name__ == "__main__":
    unittest.main()