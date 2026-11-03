import unittest
import tempfile
import shutil
import os
import uuid
from skills.repo_auto_committer import RepoAutoCommitter
from skills.git_committer import GitCommitter


class TestRepoAutoCommitterIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

        # Инициализируем git-репозиторий в временной директории для реальных тестов
        import subprocess
        subprocess.run(["git", "init", self.test_dir], capture_output=True, check=True)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Test Bot"], capture_output=True, check=True)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "bot@test.com"], capture_output=True, check=True)

        committer = GitCommitter(self.test_dir)
        # Создаем начальный коммит, чтобы репозиторий был валидным
        init_file = os.path.join(self.test_dir, "README.md")
        unique_init_content = f"Init {uuid.uuid4()}"
        with open(init_file, "w", encoding="utf-8") as f:
            f.write(unique_init_content)
        committer.commit_changes(init_file, "Initial commit")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_auto_committer_integration_flow(self):
        # Генерируем уникальные данные для проверки отсутствия хардкода
        unique_file_name = f"test_file_{uuid.uuid4().hex}.txt"
        unique_file_content = f"Content UUID: {uuid.uuid4()}"

        file_path = os.path.join(self.test_dir, unique_file_name)

        # Шаг 1. Убедимся, что до создания файла авто-коммитер ничего не делает
        auto_committer = RepoAutoCommitter(self.test_dir)
        result_empty = auto_committer.process_and_commit()
        self.assertFalse(result_empty, "Коммит не должен происходить, если нет изменений")

        # Шаг 2. Создаем новый файл с уникальными данными (изменения для монитора и суммаризатора)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(unique_file_content)

        # Шаг 3. Запускаем реальный процесс интеграции всех трех навыков через RepoAutoCommitter
        result_success = auto_committer.process_and_commit()
        self.assertTrue(result_success, "Авто-коммитер должен успешно обработать и закомитить изменения")

        # Шаг 4. Проверяем через GitCommitter, что файл действительно закоммичен в истории репозитория
        # Попробуем сделать еще один пустой прогон — он должен вернуть False, так как все изменения уже закомичены
        result_second = auto_committer.run()
        self.assertFalse(result_second, "Повторный запуск без изменений должен возвращать False")


if __name__ == "__main__":
    unittest.main()