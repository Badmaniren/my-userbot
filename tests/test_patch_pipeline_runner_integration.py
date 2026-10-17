import unittest
import tempfile
import shutil
import os
import uuid
import random
from skills.patch_pipeline_runner import PatchPipelineRunner, PatchPipelineError
from skills.git_inspector import GitInspector


class TestPatchPipelineRunnerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        # Инициализируем git-репозиторий для реальной работы GitInspector
        os.system(f"git -C {self.repo_path} init -b main")
        os.system(f"git -C {self.repo_path} config user.name 'Test Architect'")
        os.system(f"git -C {self.repo_path} config user.email 'architect@test.com'")
        
        # Создаем начальный файл с уникальным содержимым
        self.target_filename = f"file_{uuid.uuid4().hex[:8]}.py"
        self.target_file_path = os.path.join(self.repo_path, self.target_filename)
        
        self.initial_content = f"# Initial content {uuid.uuid4()}\ndef foo():\n    return {random.randint(1, 100)}\n"
        with open(self.target_file_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)
            
        os.system(f"git -C {self.repo_path} add {self.target_filename}")
        os.system(f"git -C {self.repo_path} commit -m 'Initial commit'")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_pipeline_runner_integration_success(self):
        runner = PatchPipelineRunner(repo_path=self.repo_path)
        
        # Генерируем безопасный и валидный патч (простой диф или содержимое)
        random_return_value = random.randint(101, 999)
        patch_content = f"""
def foo():
    return {random_return_value}
"""

        result = runner.run_pipeline(patch_content=patch_content, target_file=self.target_filename)
        
        # Проверяем гибридный результат и интеграцию с реальным GitInspector
        self.assertTrue(result.get("success"))
        commit_history = result.get("commit_history")
        self.assertIsInstance(commit_history, list)
        self.assertGreaterEqual(len(commit_history), 1)
        
        # Проверяем доступ через ключи и атрибуты
        self.assertTrue(result["success"])
        self.assertIsNotNone(result["commit_history"])

    def test_pipeline_runner_integration_unsafe_patch(self):
        runner = PatchPipelineRunner(repo_path=self.repo_path)
        
        # Внедряем опасный/невалидный код, который должен отловить PatchEvaluator
        dangerous_marker = f"__import__('os').system('echo {uuid.uuid4()}')"
        patch_content = f"""
def dangerous_func():
    {dangerous_marker}
"""

        with self.assertRaises(PatchPipelineError):
            runner.run_pipeline(patch_content=patch_content, target_file=self.target_filename)


if __name__ == "__main__":
    unittest.main()