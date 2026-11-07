import unittest
import tempfile
import shutil
import os
import uuid
import random
import io
from skills.repo_health_optimizer import RepoHealthOptimizer


class TestRepoHealthOptimizerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        self.optimizer = RepoHealthOptimizer(self.repo_path)
        self.random_suffix = uuid.uuid4().hex[:8]
        self.random_metric_value = random.randint(10, 100)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_optimize_repository_integration(self):
        dummy_file_name = f"test_file_{self.random_suffix}.py"
        dummy_file_path = os.path.join(self.repo_path, dummy_file_name)
        with open(dummy_file_path, "w", encoding="utf-8") as f:
            f.write(f"# Random metric: {self.random_metric_value}\nprint('integration test')\n")

        result = self.optimizer.optimize_repository()

        self.assertIsInstance(result, dict)
        self.assertIn("restoration", result)
        self.assertIn("vulnerabilities", result)
        self.assertTrue(os.path.exists(dummy_file_path))

    def test_process_optimization_stream_integration(self):
        stream_content = f"stream_data_marker_{self.random_suffix}_val_{self.random_metric_value}"
        stream = io.StringIO(stream_content)

        result = self.optimizer.process_optimization_stream(stream)

        self.assertIsInstance(result, dict)
        self.assertIn("stream_restoration", result)
        self.assertIn("stream_vulnerabilities", result)

    def test_run_optimization_routine_integration(self):
        config_file = os.path.join(self.repo_path, f"config_{self.random_suffix}.json")
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(f'{{"random_id": "{self.random_suffix}", "threshold": {self.random_metric_value}}}')

        routine_flag = self.optimizer.run_optimization_routine()

        self.assertIsInstance(routine_flag, bool)
        self.assertTrue(os.path.exists(config_file))

    def test_aliases_integration(self):
        res_optimize = self.optimizer.optimize()
        res_run = self.optimizer.run()

        self.assertIsInstance(res_optimize, dict)
        self.assertIsInstance(res_run, dict)
        self.assertIn("restoration", res_optimize)
        self.assertIn("vulnerabilities", res_run)


if __name__ == "__main__":
    unittest.main()