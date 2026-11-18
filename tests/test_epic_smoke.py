import unittest
import os
import shutil
import tempfile
from skills.git_committer import GitCommitter

class TestGitCommitterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = os.path.join(self.test_dir, "test_repo")
        os.makedirs(self.repo_path)

        # Инициализация фиктивного репозитория для проверки работы модуля
        import subprocess
        subprocess.run(["git", "init"], cwd=self.repo_path, check=True)

        self.committer = GitCommitter(self.repo_path)
        self.test_file = os.path.join(self.repo_path, "data.log")

        # Создаем реалистичный лог-файл (20 строк)
        with open(self.test_file, "w") as f:
            for i in range(1, 21):
                f.write(f"2023-10-27 10:00:{i:02d} [INFO] Processed batch {i}\n")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_commit_pipeline_stability(self):
        """
        Проверка стабильности конвейера:
        1. Чтение данных.
        2. Интеграция с файловой системой.
        3. Выполнение коммита через модуль.
        """
        print(f"\n[ПРОВЕРКА] Начало теста в директории: {self.repo_path}")

        # Проверка содержимого файла
        with open(self.test_file, "r") as f:
            lines = f.readlines()
            print(f"[ПРОВЕРКА] Файл создан, строк: {len(lines)}")
            print(f"[ПРОВЕРКА] Последняя запись: {lines[-1].strip()}")

        # Выполнение коммита через модуль
        message = "feat: add batch processing logs"
        success = self.committer.commit_changes(self.test_file, message)

        print(f"[ПРОВЕРКА] Результат commit_changes: {success}")
        self.assertTrue(success, "Модуль git_committer не смог выполнить коммит")

        # Проверка статуса через git (подтверждение интеграции)
        import subprocess
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            cwd=self.repo_path,
            capture_output=True,
            text=True
        )

        print(f"[ПРОВЕРКА] Реальный коммит в git: {result.stdout.strip()}")
        self.assertIn(message, result.stdout)
        print("[ПРОВЕРКА] Конвейер автокоммитов успешно прошел проверку.")

if __name__ == "__main__":
    unittest.main()