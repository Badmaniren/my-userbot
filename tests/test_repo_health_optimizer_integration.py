import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.repo_health_optimizer import RepoHealthOptimizer

class TestRepoHealthOptimizerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.random_tag = str(uuid.uuid4())
        
        # Создаем минимальную структуру репозитория и файлы для реальной работы навыков
        with open(os.path.join(self.test_dir, "requirements.txt"), "w") as f:
            f.write(f"requests=={random.randint(2, 3)}.{random.randint(0, 10)}.{random.randint(0, 5)}\n")
            
        os.makedirs(os.path.join(self.test_dir, ".git"), exist_ok=True)
        with open(os.path.join(self.test_dir, ".git", "config"), "w") as f:
            f.write(f"[core]\n\trepositoryformatversion = 0\n\tcomment = {self.random_tag}\n")

        self.optimizer = RepoHealthOptimizer(self.test_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_optimize_repository_integration(self):
        result = self.optimizer.optimize_repository()
        
        self.assertIsInstance(result, dict)
        self.assertIn("restoration", result)
        self.assertIn("vulnerabilities", result)
        
        restoration_data = result["restoration"]
        vulnerability_data = result["vulnerabilities"]
        
        self.assertIsInstance(restoration_data, dict)
        self.assertIsInstance(vulnerability_data, dict)

    def test_process_optimization_stream_integration(self):
        stream_data = f"stream_log_{self.random_tag}_action"
        result = self.optimizer.process_optimization_stream(stream_data)
        
        self.assertIsInstance(result, dict)
        self.assertIn("stream_restoration", result)
        self.assertIn("stream_vulnerabilities", result)
        
        self.assertIsInstance(result["stream_restoration"], dict)

    def test_run_optimization_routine_integration(self):
        routine_flag = self.optimizer.run_optimization_routine()
        self.assertIsInstance(routine_flag, bool)

    def test_aliases_integration(self):
        res_optimize = self.optimizer.optimize()
        res_run = self.optimizer.run()
        
        self.assertIsInstance(res_optimize, dict)
        self.assertIsInstance(res_run, dict)
        self.assertIn("restoration", res_optimize)
        self.assertIn("vulnerabilities", res_run)

if __name__ == "__main__":
    unittest.main()