import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_performance_profiler_pipeline import repo_performance_profiler_pipeline
from skills.repo_monitor import RepoMonitor
from skills.repo_health_diagnostic import RepoHealthDiagnostic

class TestRepoPerformanceProfilerPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        # Инициализация простого репозитория для тестов
        os.system(f"git -C {self.repo_path} init -b main")
        os.system(f"git -C {self.repo_path} config user.name 'Test Architect'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com'")
        
        # Создаем случайный файл с уникальным содержимым
        self.unique_file_name = f"perf_test_{uuid.uuid4().hex[:8]}.py"
        self.unique_file_path = os.path.join(self.repo_path, self.unique_file_name)
        
        self.random_content = f"# Performance test file\nVALUE = {random.randint(1000, 9999)}\n"
        with open(self.unique_file_path, "w", encoding="utf-8") as f:
            f.write(self.random_content)
            
        os.system(f"git -C {self.repo_path} add {self.unique_file_name}")
        os.system(f"git -C {self.repo_path} commit -m 'Initial commit for performance profiling'")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_performance_profiler_pipeline_integration(self):
        profiling_id = str(uuid.uuid4())
        threshold_value = random.uniform(0.5, 0.99)
        
        # Вызов тестируемого модуля-пайплайна
        result = repo_performance_profiler_pipeline(
            repo_path=self.repo_path,
            profiling_id=profiling_id,
            threshold=threshold_value
        )
        
        # Проверяем структуру и наличие данных от реальных интегрированных навыков
        self.assertIsInstance(result, dict)
        self.assertIn("profiling_id", result)
        self.assertEqual(result["profiling_id"], profiling_id)
        
        self.assertIn("monitor_status", result)
        self.assertIn("diagnostic_data", result)
        self.assertIn("is_performant", result)
        
        # Прямая проверка работы интегрированных модулей внутри пайплайна без моков
        monitor = RepoMonitor(self.repo_path)
        status = monitor.check_status()
        self.assertIsInstance(status, str)
        
        diagnostic = RepoHealthDiagnostic()
        full_diag = diagnostic.run_full_diagnostic(self.repo_path)
        self.assertIsInstance(full_diag, dict)
        
        # Убеждаемся, что порог и метрики действительно анализируются
        metric_evaluation = diagnostic.evaluate_threshold(full_diag, "health_score", threshold_value)
        self.assertIsInstance(metric_evaluation, bool)

if __name__ == "__main__":
    unittest.main()