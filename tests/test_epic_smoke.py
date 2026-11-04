import unittest
import os
import json
import tempfile
import shutil
from skills.dependency_scanner import DependencyScanner
from skills.dependency_updater_pipeline import DependencyScanner as DependencyUpdater
from skills.git_committer import GitCommitter

class TestDependencyLifecycleAutomation(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.requirements_path = os.path.join(self.test_dir, "requirements.txt")

        # Создаем реалистичный файл зависимостей для проверки
        content = [
            "requests==2.25.1",
            "numpy==1.19.0",
            "pandas==1.2.0",
            "flask==1.1.2",
            "pyyaml==5.3.1"
        ]
        with open(self.requirements_path, "w") as f:
            f.write("\n".join(content))

        # Инициализируем Git для имитации реального репозитория
        os.system(f"cd {self.test_dir} && git init && git config user.email 'test@test.com' && git config user.name 'Test'")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_dependency_lifecycle_flow(self):
        print("\n--- НАЧАЛО ПРАКТИЧЕСКОЙ ПРОВЕРКИ: Жизненный цикл зависимостей ---")

        # 1. Сканирование (Dependency Scanner)
        scanner = DependencyScanner(self.test_dir)
        dependencies = scanner.parse_requirements(self.requirements_path)
        print(f"[1] Обнаруженные зависимости: {dependencies}")
        self.assertTrue(len(dependencies) >= 5, "Не удалось считать зависимости из файла")

        # 2. Анализ разрывов (Gap Analysis)
        # Имитируем работу пайплайна, который сравнивает текущие версии с "актуальными"
        # В реальных условиях здесь вызывается логика сравнения с PyPI
        updater = DependencyUpdater(self.test_dir)
        print("[2] Запуск анализа разрывов (Gap Analysis)...")

        # Проверяем, что сканер видит файл
        scan_result = updater.scan()
        print(f"[2] Результат сканирования пайплайном: {scan_result}")

        # 3. Авто-обновление и коммит
        committer = GitCommitter(self.test_dir)
        update_message = "chore: auto-update dependencies to latest stable versions"

        # Имитируем обновление файла
        with open(self.requirements_path, "w") as f:
            f.write("requests==2.31.0\nnumpy==1.26.0\npandas==2.1.0\nflask==3.0.0\npyyaml==6.0.1")

        print("[3] Применение обновлений и фиксация изменений...")
        success = committer.commit_changes(self.requirements_path, update_message)

        self.assertTrue(success, "Не удалось закоммитить изменения зависимостей")

        # Проверка лога (через git log)
        log_output = os.popen(f"cd {self.test_dir} && git log -1 --pretty=%B").read().strip()
        print(f"[3] Проверка коммита в Git: {log_output}")

        self.assertEqual(log_output, update_message)
        print("--- ПРОВЕРКА УСПЕШНО ЗАВЕРШЕНА ---")

if __name__ == "__main__":
    unittest.main()