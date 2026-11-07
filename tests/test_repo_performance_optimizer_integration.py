import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.repo_performance_optimizer import RepoPerformanceOptimizer


class TestRepoPerformanceOptimizerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        self.profiling_threshold = round(random.uniform(0.1, 5.0), 2)
        
        self.optimizer = RepoPerformanceOptimizer(
            repo_path=self.repo_path,
            threshold=self.profiling_threshold
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_integration_performance_optimizer_workflow(self):
        dummy_file_name = f"test_source_{uuid.uuid4().hex[:8]}.py"
        dummy_file_path = os.path.join(self.repo_path, dummy_file_name)
        
        random_content = f"# Performance test file\n# UUID: {uuid.uuid4()}\nvalue = {random.randint(100, 999)}\n"
        with open(dummy_file_path, "w", encoding="utf-8") as f:
            f.write(random_content)

        self.assertTrue(os.path.exists(dummy_file_path), "Тестовый файл должен быть создан в репозитории")

        result = self.optimizer.optimize()

        self.assertIsInstance(result, dict, "Результат оптимизации должен быть словарем")
        
        has_profiling_data = any(
            key in result for key in ["profiling", "profiling_pipeline", "profile", "metrics"]
        )
        has_optimization_data = any(
            key in result for key in ["optimization", "optimized", "health", "status", "results"]
        )
        
        self.assertTrue(
            has_profiling_data or has_optimization_data,
            f"Результат должен содержать данные профилирования или оптимизации. Получено: {result.keys()}"
        )

        if hasattr(self.optimizer, "run_performance_optimization_pipeline"):
            pipeline_result = self.optimizer.run_performance_optimization_pipeline()
            self.assertIsInstance(pipeline_result, dict, "Результат пайплайна должен быть словарем")


if __name__ == "__main__":
    unittest.main()