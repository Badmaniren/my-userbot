import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.repo_reporter import RepoReporter
from skills.repo_performance_optimizer import RepoPerformanceOptimizer
from skills.repo_performance_dashboard import RepoPerformanceDashboard

class TestRepoPerformanceDashboardIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.unique_id = str(uuid.uuid4())
        self.random_threshold = random.randint(50, 500)
        
        # Создаем минимальную структуру репозитория для работы навыков
        os.makedirs(os.path.join(self.repo_path, ".git"), exist_ok=True)
        
        # Инициализируем реальные компоненты композиции без моков
        self.reporter = RepoReporter(repo_path=self.repo_path)
        self.optimizer = RepoPerformanceOptimizer(repo_path=self.repo_path, threshold=self.random_threshold)
        
        # Инициализируем тестируемый модуль панели мониторинга
        self.dashboard = RepoPerformanceDashboard(
            repo_path=self.repo_path,
            reporter=self.reporter,
            optimizer=self.optimizer
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_performance_dashboard_integration(self):
        # Генерируем случайные данные для потока производительности
        stream_metric_name = f"metric_{self.unique_id}"
        stream_metric_value = random.uniform(10.0, 1000.0)
        stream_data = {
            "metric": stream_metric_name,
            "value": stream_metric_value,
            "run_id": self.unique_id
        }

        # 1. Проверяем обработку потока данных оптимизатором через панель
        stream_result = self.dashboard.handle_dashboard_stream(stream_data)
        self.assertIsInstance(stream_result, dict)

        # 2. Запускаем рутинную оптимизацию производительности
        routine_success = self.dashboard.execute_routine_monitoring()
        self.assertIsInstance(routine_success, bool)

        # 3. Выполняем полный цикл оптимизации и генерации отчета через композицию
        dashboard_report_data = self.dashboard.generate_live_dashboard_report(
            status="INTEGRATION_TEST_SUCCESS",
            summary=f"Running live performance tracking for ID: {self.unique_id}"
        )

        self.assertIn("report_path", dashboard_report_data)
        report_file_path = dashboard_report_data["report_path"]

        # Проверяем, что файл отчета реально создан на диске
        self.assertTrue(os.path.exists(report_file_path))

        # Читаем реальный файл отчета и проверяем наличие уникальных данных
        with open(report_file_path, "r", encoding="utf-8") as f:
            report_content = f.read()

        self.assertIn(self.unique_id, report_content)
        self.assertIn("INTEGRATION_TEST_SUCCESS", report_content)

if __name__ == "__main__":
    unittest.main()