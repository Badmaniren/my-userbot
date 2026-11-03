import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_notifier import RepoNotifier

class TestRepoNotifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        
        # Инициализация git репозитория для тестов
        os.system(f"git -C {self.test_dir} init -b main")
        os.system(f"git -C {self.test_dir} config user.name 'Test User'")
        os.system(f"git -C {self.test_dir} config user.email 'test@example.com'")
        
        # Создаем начальный коммит, чтобы репозиторий не был пустым
        self.init_file = os.path.join(self.test_dir, "README.md")
        with open(self.init_file, "w", encoding="utf-8") as f:
            f.write("# Initial state")
        os.system(f"git -C {self.test_dir} add README.md")
        os.system(f"git -C {self.test_dir} commit -m 'Initial commit'")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_repo_notifier_real_integration(self):
        # Генерируем уникальные случайные данные для проверки сквозной передачи
        unique_id = str(uuid.uuid4())
        random_prefix = f"data_{random.randint(1000, 9999)}"
        file_name = f"{random_prefix}_{unique_id}.txt"
        file_path = os.path.join(self.test_dir, file_name)
        
        random_content = f"Random content UUID: {unique_id}"
        
        # Создаем файл сгенерированными данными, чтобы спровоцировать изменения для автокоммита и отчета
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(random_content)

        # Инициализируем тестируемый модуль (композиция без моков)
        notifier = RepoNotifier(self.test_dir)
        
        # Вызываем метод уведомления/обработки, который должен задействовать repo_auto_committer и repo_reporter
        # Проверяем, что процесс завершился успешно (True)
        result = notifier.notify_and_commit()
        self.assertTrue(result, "Модуль RepoNotifier должен успешно выполнить процесс коммита и отчета")

        # Проверяем реальные изменения: автокоммит должен был закоммитить новый файл
        git_status_output = os.popen(f"git -C {self.test_dir} status --porcelain").read()
        self.assertEqual(git_status_output.strip(), "", "Репозиторий должен быть чистым после автокоммита")

        git_log = os.popen(f"git -C {self.test_dir} log -n 1 --pretty=format:'%s'").read()
        self.assertTrue(len(git_log) > 0, "В репозитории должен появиться новый коммит")

        # Проверяем реальное появление и содержимое сгенерированного отчета (работа repo_reporter в составе композиции)
        report_files = [f for f in os.listdir(self.test_dir) if "report" in f.lower() or f.endswith(".md") or f.endswith(".txt")]
        # Исключаем наш исходный файл
        report_files = [f for f in report_files if f != file_name and f != "README.md"]
        
        self.assertGreaterEqual(len(report_files), 1, "Должен быть сгенерирован хотя бы один файл отчета")
        
        report_path = os.path.join(self.test_dir, report_files[0])
        with open(report_path, "r", encoding="utf-8") as rf:
            report_text = rf.read()
            
        # Проверяем, что уникальный ID попал в сгенерированный отчет сквозным образом
        self.assertIn(unique_id, report_text, f"Отчет должен содержать уникальный сгенерированный идентификатор {unique_id}")

if __name__ == "__main__":
    unittest.main()