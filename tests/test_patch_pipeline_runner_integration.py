import unittest
import tempfile
import shutil
import os
import uuid
import random

from skills.patch_pipeline_runner import PatchPipelineRunner
from skills.patch_evaluator import PatchEvaluator, PatchEvaluationResult
from skills.git_inspector import GitInspector

class TestPatchPipelineRunnerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        # Инициализируем простейший git репозиторий для реальной работы git_inspector
        os.system(f"git -C {self.repo_path} init -b main")
        os.system(f"git -C {self.repo_path} config user.name 'Test User'")
        os.system(f"git -C {self.repo_path} config user.email 'test@example.com'")
        
        self.target_file_name = f"code_{uuid.uuid4().hex[:8]}.py"
        self.target_file_path = os.path.join(self.repo_path, self.target_file_name)
        
        self.random_string = f"print('{uuid.uuid4()}')"
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(self.random_string + "\n")
            
        os.system(f"git -C {self.repo_path} add {self.target_file_name}")
        os.system(f"git -C {self.repo_path} commit -m 'Initial commit {uuid.uuid4()}'")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_pipeline_runner_end_to_end(self):
        unique_patch_token = f"val_{uuid.uuid4().hex}"
        patch_content = f"# {unique_patch_token}\nx = {random.randint(1, 100)}\n"
        
        runner = PatchPipelineRunner(repo_path=self.repo_path)
        
        # Проверяем композицию: внутри пайплайна должны использоваться реальные компоненты
        self.assertIsInstance(runner.evaluator, PatchEvaluator)
        self.assertIsInstance(runner.inspector, GitInspector)
        
        result = runner.run_pipeline(patch_content=patch_content, target_file=self.target_file_name)
        
        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(hasattr(result, "is_safe"))
        self.assertTrue(hasattr(result, "is_valid"))
        
        history = runner.inspector.get_commit_history(max_count=10)
        self.assertGreaterEqual(len(history), 1)

if __name__ == "__main__":
    unittest.main()