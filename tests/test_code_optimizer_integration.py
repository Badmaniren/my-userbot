import unittest
import tempfile
import shutil
import os
import uuid
import random
import subprocess
from skills.code_optimizer import CodeOptimizer
from skills.patch_executor import PatchExecutor
from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser

class TestCodeOptimizerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        subprocess.run(["git", "init"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "architect@test.com"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Architect Test"], cwd=self.repo_path, check=True, capture_output=True)

        self.random_id = str(uuid.uuid4())
        self.unused_var_name = f"var_{random.randint(1000, 9999)}"

        self.file_name = f"module_{self.random_id}.py"
        self.file_path = os.path.join(self.repo_path, self.file_name)

        initial_content = f"import os\nimport sys\n\n{self.unused_var_name} = 42\n\ndef run():\n    print('{self.random_id}')\n"

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(initial_content)

        subprocess.run(["git", "add", self.file_name], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"Initial commit {self.random_id}"], cwd=self.repo_path, check=True, capture_output=True)

        self.git_inspector = GitInspector(self.repo_path)
        self.lesson_parser = LessonParser(self.git_inspector)
        self.patch_executor = PatchExecutor(self.repo_path, self.git_inspector, self.lesson_parser)
        self.code_optimizer = CodeOptimizer(self.repo_path, self.patch_executor, self.git_inspector)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_integration_code_optimizer_workflow(self):
        optimization_result = self.code_optimizer.optimize_code()

        self.assertIsInstance(optimization_result, dict)

        with open(self.file_path, "r", encoding="utf-8") as f:
            optimized_content = f.read()

        self.assertNotIn("import sys", optimized_content)
        self.assertIn(self.random_id, optimized_content)

        latest_changes = self.git_inspector.get_latest_changes()
        self.assertIsNotNone(latest_changes)

if __name__ == "__main__":
    unittest.main()