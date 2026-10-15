import unittest
import tempfile
import shutil
import os
import uuid
import random
import subprocess

from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser
from skills.hypothesis_generator import HypothesisGenerator
from skills.patch_executor import PatchExecutor

class TestPatchExecutorIntegration(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        
        subprocess.run(["git", "init"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=self.repo_path, check=True, capture_output=True)
        
        self.unique_id = str(uuid.uuid4())
        self.target_filename = f"lesson_{random.randint(1000, 9999)}.py"
        self.file_path = os.path.join(self.repo_path, self.target_filename)
        
        initial_content = f"# Lesson ID: {self.unique_id}\nprint('Initial code')\n"
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(initial_content)
            
        subprocess.run(["git", "add", self.target_filename], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", f"Add lesson {self.unique_id}"], cwd=self.repo_path, check=True, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_patch_executor_integration_flow(self):
        inspector = GitInspector(repo_path=self.repo_path)
        parser = LessonParser(git_inspector=inspector)
        generator = HypothesisGenerator(git_inspector=inspector, lesson_parser=parser)
        executor = PatchExecutor(git_inspector=inspector)

        hypotheses = generator.generate_hypotheses(max_commits=1)
        prioritized = generator.prioritize_hypotheses(hypotheses)

        new_content_marker = str(uuid.uuid4())
        
        patch_payload = {
            "file_path": self.target_filename,
            "content": f"# Patched ID: {new_content_marker}\nprint('Updated code')\n",
            "mode": "overwrite"
        }

        execution_result = executor.apply_patch(patch_payload)

        self.assertTrue(execution_result, "PatchExecutor did not apply the patch successfully.")

        with open(self.file_path, "r", encoding="utf-8") as f:
            updated_file_content = f.read()

        self.assertIn(new_content_marker, updated_file_content, "Real changes were not detected in the target file after patch execution.")

        latest_changes = inspector.get_latest_changes()
        self.assertIsNotNone(latest_changes, "GitInspector failed to read repository state after patch execution.")