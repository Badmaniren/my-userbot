import unittest
import tempfile
import shutil
import os
import uuid
import random
import subprocess

from skills.autonomous_engine import AutonomousEngine
from skills.hypothesis_generator import HypothesisGenerator
from skills.patch_executor import PatchExecutor
from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser

class TestAutonomousEngineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        subprocess.run(["git", "init"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Test Bot"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "bot@test.com"], cwd=self.repo_path, check=True, capture_output=True)

        self.random_file_name = f"module_{uuid.uuid4().hex[:8]}.py"
        self.file_path = os.path.join(self.repo_path, self.random_file_name)

        self.initial_content = f"# Initial content {uuid.uuid4()}\ndef buggy_func():\n    pass\n"
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(self.initial_content)

        subprocess.run(["git", "add", self.random_file_name], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=self.repo_path, check=True, capture_output=True)

        self.lesson_content = f"LESSON: Fix bug in {self.random_file_name}\nDIFF: change pass to return {random.randint(100, 999)}"
        self.lesson_file_path = os.path.join(self.repo_path, "lessons.txt")
        with open(self.lesson_file_path, "w", encoding="utf-8") as f:
            f.write(self.lesson_content)

        subprocess.run(["git", "add", "lessons.txt"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "Add lessons file"], cwd=self.repo_path, check=True, capture_output=True)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_autonomous_engine_integration_pipeline(self):
        git_inspector = GitInspector(repo_path=self.repo_path)
        lesson_parser = LessonParser(git_inspector=git_inspector)
        hypothesis_generator = HypothesisGenerator(git_inspector=git_inspector, lesson_parser=lesson_parser)
        patch_executor = PatchExecutor(repo_path=self.repo_path, git_inspector=git_inspector, lesson_parser=lesson_parser)

        engine = AutonomousEngine(
            repo_path=self.repo_path,
            git_inspector=git_inspector,
            lesson_parser=lesson_parser,
            hypothesis_generator=hypothesis_generator,
            patch_executor=patch_executor
        )

        self.assertTrue(hasattr(engine, "run_cycle") or hasattr(engine, "execute") or hasattr(engine, "analyze_and_fix"))

        hypotheses = hypothesis_generator.generate_hypotheses(max_commits=5)
        prioritized = hypothesis_generator.prioritize_hypotheses(hypotheses)

        self.assertIsInstance(prioritized, list)

        execution_result = patch_executor.execute_from_lessons()
        self.assertIsInstance(execution_result, dict)

        if hasattr(engine, "run_cycle"):
            res = engine.run_cycle()
        elif hasattr(engine, "execute"):
            res = engine.execute()
        else:
            res = engine.analyze_and_fix()

        self.assertIsNotNone(res)

        with open(self.file_path, "r", encoding="utf-8") as f:
            updated_content = f.read()

        self.assertNotEqual(updated_content, self.initial_content)

if __name__ == "__main__":
    unittest.main()