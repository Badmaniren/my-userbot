import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.git_inspector import GitInspector
from skills.patch_evaluator import PatchEvaluator, PatchEvaluationResult
from skills.patch_pipeline_executor import PatchPipelineExecutor

class TestPatchPipelineExecutorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        # Инициализация простого git репозитория для тестов без использования моков
        os.system(f"git -C {self.repo_path} init -b main")
        os.system(f"git -C {self.repo_path} config user.name 'Test User'")
        os.system(f"git -C {self.repo_path} config user.email 'test@example.com'")

        self.target_file_name = f"file_{uuid.uuid4().hex[:8]}.py"
        self.target_file_path = os.path.join(self.repo_path, self.target_file_name)

        self.initial_content = f"# Initial content {uuid.uuid4()}\nx = {random.randint(1, 100)}\n"
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)

        os.system(f"git -C {self.repo_path} add {self.target_file_name}")
        os.system(f"git -C {self.repo_path} commit -m 'Initial commit'")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_pipeline_execution_integration(self):
        random_val = random.randint(100, 999)
        patch_content = f"print('Executing pipeline test {random_val}')\nx = {random_val}\n"

        pipeline = PatchPipelineExecutor(repo_path=self.repo_path)

        # Проверяем композицию: внутри пайплайна должны реально использоваться GitInspector и PatchEvaluator
        self.assertIsInstance(pipeline.git_inspector, GitInspector)
        self.assertIsInstance(pipeline.patch_evaluator, PatchEvaluator)

        result = pipeline.execute(patch_content=patch_content, target_file=self.target_file_name)

        self.assertIsInstance(result, PatchEvaluationResult)
        self.assertTrue(hasattr(result, "is_safe"))
        self.assertTrue(hasattr(result, "is_valid"))

        # Проверяем, что git_inspector фиксирует состояние репозитория в рамках пайплайна
        repo_analysis = pipeline.git_inspector.analyze_repository()
        self.assertIsInstance(repo_analysis, dict)

        # Проверяем, что изменения отразились на целевом файле или пайплайн корректно обработал его
        with open(self.target_file_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn(str(random_val), content)

if __name__ == "__main__":
    unittest.main()