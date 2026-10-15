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
from skills.autonomous_engine import AutonomousEngine


class TestAutonomousEngineIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix=f"auto_engine_test_{uuid.uuid4().hex}_")
        self._init_git_repo(self.test_dir)

        self.rand_filename = f"module_{uuid.uuid4().hex[:8]}.py"
        self.rand_content = f"# Lesson: Fix bug {uuid.uuid4()}\nprint('{uuid.uuid4()}')\n"
        self.file_path = os.path.join(self.test_dir, self.rand_filename)

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(self.rand_content)

        self._git_add_and_commit(self.test_dir, f"Initial commit {uuid.uuid4()}")

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _init_git_repo(self, path):
        subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Test Bot"], cwd=path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "bot@test.com"], cwd=path, capture_output=True, check=True)

    def _git_add_and_commit(self, path, message):
        subprocess.run(["git", "add", "."], cwd=path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", message], cwd=path, capture_output=True, check=True)

    def test_autonomous_engine_closed_loop_integration(self):
        engine = AutonomousEngine(repo_path=self.test_dir)

        self.assertIsInstance(engine.git_inspector, GitInspector)
        self.assertIsInstance(engine.lesson_parser, LessonParser)
        self.assertIsInstance(engine.hypothesis_generator, HypothesisGenerator)
        self.assertIsInstance(engine.patch_executor, PatchExecutor)

        modified_content = self.rand_content + f"\n# Additional update {uuid.uuid4()}\n"
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(modified_content)
        self._git_add_and_commit(self.test_dir, f"Update commit {uuid.uuid4()}")

        result = engine.run_autonomous_cycle()

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("applied_patches", result)

        latest_changes = engine.git_inspector.get_latest_changes()
        self.assertIsNotNone(latest_changes)

        history = engine.git_inspector.get_commit_history(max_count=random.randint(2, 5))
        self.assertGreaterEqual(len(history), 2)


if __name__ == "__main__":
    unittest.main()