import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_audit_dispatcher import RepoAuditDispatcher

class TestRepoAuditDispatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()
        self.random_id = str(uuid.uuid4())
        self.test_file_name = f"audit_target_{self.random_id}.txt"
        self.test_file_path = os.path.join(self.test_dir, self.test_file_name)
        
        # Генерация случайных входных данных для проверки отсутствия хардкода
        self.metric_value = random.randint(10, 100)
        self.synthetic_payload = {
            "id": self.random_id,
            "metric": self.metric_value,
            "status": "integration_test"
        }
        
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write(f"Test audit content for ID: {self.random_id}\nMetric: {self.metric_value}")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.rmtree(self.output_dir, ignore_errors=True)

    def test_dispatcher_real_composition(self):
        # Инициализация тестируемого диспетчера комплексного аудита (композиция реальных навыков)
        dispatcher = RepoAuditDispatcher(
            repository_path=self.test_dir,
            output_dir=self.output_dir
        )

        # Вызов процесса диспетчеризации и проверки здоровья репозитория
        health_dispatch_result = dispatcher.dispatch_health(self.test_file_path)
        self.assertIsInstance(health_dispatch_result, bool)

        # Вызов критической проверки с уникальными случайными данными
        critical_check_result = dispatcher.check_critical_metric(
            title=f"Critical Audit {self.random_id}",
            value=self.metric_value,
            file_path=self.test_file_path
        )
        self.assertIsInstance(critical_check_result, bool)

        # Комплексный синтез аудита с использованием реального синтезатора
        synthesis_result = dispatcher.run_full_synthesis(self.synthetic_payload)
        self.assertIsInstance(synthesis_result, dict)
        
        # Проверяем, что синтезатор вернул уникальные данные, завязанные на переданный payload
        self.assertIn("id", synthesis_result)
        self.assertEqual(synthesis_result["id"], self.random_id)

        # Экспорт отчета через синтезатор и проверка реального появления файла
        export_filename = f"report_{self.random_id}.json"
        exported_path = dispatcher.export_audit_report(
            target_path=self.output_dir,
            synthesis_result=synthesis_result,
            filename=export_filename
        )

        self.assertTrue(os.path.exists(exported_path), "Экспортированный отчет должен реально существовать в файловой системе")
        
        with open(exported_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.random_id, content, "Файл отчета должен содержать уникальный UUID текущего теста")

if __name__ == "__main__":
    unittest.main()