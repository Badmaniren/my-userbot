import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.repo_audit_aggregator_pipeline import run_audit_aggregator_pipeline
from skills.repo_audit_synthesizer import RepoAuditSynthesizer
from skills.repo_monitor import RepoMonitor, GitCommitter

class TestRepoAuditAggregatorPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        # Инициализируем git репозиторий для корректной работы RepoMonitor и GitCommitter
        os.system(f"git -C {self.repo_path} init -b main")
        os.system(f"git -C {self.repo_path} config user.name 'Test Architect'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com'")
        
        # Создаем случайный файл для мониторинга
        self.random_filename = f"audit_target_{uuid.uuid4().hex[:8]}.txt"
        self.file_path = os.path.join(self.repo_path, self.random_filename)
        
        self.random_content = f"audit_data_{random.randint(1000, 9999)}"
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(self.random_content)

        # Коммитим файл, чтобы монитор видел чистый статус или изменения
        committer = GitCommitter(self.repo_path)
        committer.commit_changes(self.random_filename, "Initial commit for integration test")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_repo_audit_aggregator_pipeline_integration(self):
        output_dir = os.path.join(self.test_dir, f"output_{uuid.uuid4().hex[:6]}")
        os.makedirs(output_dir, exist_ok=True)
        
        synthetic_id = str(uuid.uuid4())
        synthetic_payload = {
            "id": synthetic_id,
            "metric": random.randint(1, 100),
            "status": "active"
        }

        # Вызываем тестируемый конвейер интеграционно без моков
        result = run_audit_aggregator_pipeline(
            repository_path=self.repo_path,
            output_dir=output_dir,
            synthetic_payload=synthetic_payload
        )

        # Проверяем, что конвейер вернул результат и использовал переданные данные
        self.assertIsInstance(result, dict)
        self.assertIn("synthesis", result)
        self.assertIn("monitor", result)

        # Проверяем реальное поведение зависимых навыков (RepoAuditSynthesizer и RepoMonitor)
        synthesizer = RepoAuditSynthesizer()
        self.assertTrue(hasattr(synthesizer, "synthesize"))

        monitor = RepoMonitor(self.repo_path)
        status = monitor.check_status()
        self.assertIsInstance(status, str)

        # Проверяем появление файлов отчета на диске
        exported_files = os.listdir(output_dir)
        self.assertGreater(len(exported_files), 0, "Конвейер должен был экспортировать отчеты в output_dir")

if __name__ == "__main__":
    unittest.main()