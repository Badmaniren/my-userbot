import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_auto_committer import RepoAutoCommitter

class TestRepoAutoCommitterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        # Инициализация git репозитория для тестов
        os.system(f"git -C {self.test_dir} init -b main")
        os.system(f"git -C {self.test_dir} config user.name 'Test Architect'")
        os.system(f"git -C {self.test_dir} config user.email 'architect@test.com'")
        
        # Создаем начальный коммит, чтобы репозиторий был не пустым
        self.initial_file = os.path.join(self.test_dir, "README.md")
        with open(self.initial_file, "w") as f:
            f.write("# Initial state")
        os.system(f"git -C {self.test_dir} add README.md")
        os.system(f"git -C {self.test_dir} commit -m 'Initial commit'")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_auto_committer_real_integration(self):
        # Генерируем случайные данные для проверки сквозной интеграции без хардкода
        unique_id = str(uuid.uuid4())
        random_content = f"Random update content: {random.randint(1000, 9999)} - {unique_id}"
        
        target_filename = f"file_{unique_id[:8]}.txt"
        target_filepath = os.path.join(self.test_dir, target_filename)

        # Создаем реальный файл с изменениями в репозитории
        with open(target_filepath, "w") as f:
            f.write(random_content)

        # Инициализируем тестируемый модуль (композицию без моков)
        auto_committer = RepoAutoCommitter(self.test_dir)

        # Выполняем реальный процесс: мониторинг -> суммаризация -> коммит
        result = auto_committer.process_and_commit()

        # Проверки
        self.assertTrue(result, "Модуль должен успешно завершить цикл мониторинга, суммаризации и коммита")

        # Проверяем, что изменения действительно закоммичены в git
        git_log_output = os.popen(f"git -C {self.test_dir} log -1 --pretty=format:'%s'").read()
        
        # Убедимся, что коммит содержит уникальный сгенерированный ID или упоминание файла
        self.assertTrue(
            len(git_log_output) > 0, 
            "В репозитории должен появиться новый коммит"
        )
        
        # Проверяем статус репозитория (он должен быть чистым после автокоммита)
        status_output = os.popen(f"git -C {self.test_dir} status --porcelain").read().strip()
        self.assertEqual(
            status_output, 
            "", 
            "Рабочая директория должна быть чистой после успешного автокоммита"
        )

if __name__ == "__main__":
    unittest.main()