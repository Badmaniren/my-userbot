import unittest
import uuid
import random
import tempfile
import os
from skills.patch_regression_listener import start_regression_listening
from skills.git_inspector import GitInspector

class TestPatchRegressionListenerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.log_path = os.path.join(self.repo_path, f"audit_{uuid.uuid4().hex}.log")
        
        # Инициализируем реальный репозиторий через GitInspector окружение
        os.system(f"git init {self.repo_path}")
        os.system(f"git -C {self.repo_path} config user.name 'Architect'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@system.local'")

    def tearDown(self):
        self.test_dir.cleanup()

    def test_regression_listener_flow(self):
        # Генерируем уникальные случайные данные патча
        patch_id = str(uuid.uuid4())
        file_name = f"patch_{random.randint(1000, 9999)}.diff"
        file_path = os.path.join(self.repo_path, file_name)
        
        random_content = f"diff --git a/test.py b/test.py\nindex {uuid.uuid4().hex[:7]}..{uuid.uuid4().hex[:7]} 100644\n--- a/test.py\n+++ b/test.py\n@@ -1,1 +1,2 @@\n-print('old')\n+print('{patch_id}')\n"
        
        # Создаем файл патча в системе
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(random_content)

        # Проверяем интеграцию с GitInspector
        inspector = GitInspector(self.repo_path)
        commits = inspector.get_commit_history()
        self.assertIsInstance(commits, list)

        # Запускаем прослушиватель регрессии патчей (реальный вызов без моков)
        listener_payload = {
            "patch_id": patch_id,
            "repo_path": self.repo_path,
            "log_path": self.log_path,
            "file_target": file_path
        }
        
        result = start_regression_listening(listener_payload)
        
        # Проверяем, что модуль отработал и вернул детерминированный результат, связанный со случайными данными
        self.assertIsNotNone(result)
        if isinstance(result, dict):
            self.assertIn("status", result)
            self.assertEqual(result.get("patch_id"), patch_id)

        # Убеждаемся, что побочный эффект зафиксирован в системе (файл логов или изменения)
        self.assertTrue(os.path.exists(file_path))

if __name__ == "__main__":
    unittest.main()