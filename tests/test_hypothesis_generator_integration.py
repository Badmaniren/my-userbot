import unittest
import uuid
import random
import tempfile
import os
import subprocess

from skills.hypothesis_generator import HypothesisGenerator, HypothesisGeneratorError
from skills.lesson_parser import LessonParser
from skills.git_inspector import GitInspector


class TestHypothesisGeneratorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name

        subprocess.run(["git", "init"], cwd=self.repo_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.name", "Architect"], cwd=self.repo_path, capture_output=True, check=True)
        subprocess.run(["git", "config", "user.email", "architect@system.local"], cwd=self.repo_path, capture_output=True, check=True)

        self.unique_title = f"Lesson_{uuid.uuid4().hex[:8]}"
        self.unique_content = f"Content_{random.randint(1000, 9999)}"
        self.file_name = f"lesson_{uuid.uuid4().hex[:6]}.md"

        file_path = os.path.join(self.repo_path, self.file_name)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"# {self.unique_title}\n\n{self.unique_content}")

        subprocess.run(["git", "add", self.file_name], cwd=self.repo_path, capture_output=True, check=True)
        subprocess.run(["git", "commit", "-m", f"Add {self.unique_title}"], cwd=self.repo_path, capture_output=True, check=True)

        self.git_inspector = GitInspector(self.repo_path)
        self.lesson_parser = LessonParser(self.git_inspector)
        self.hypothesis_generator = HypothesisGenerator(self.git_inspector, self.lesson_parser)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_generate_hypotheses_integration(self):
        hypotheses = self.hypothesis_generator.generate()

        self.assertIsInstance(hypotheses, list)
        self.assertGreater(len(hypotheses), 0)

        found = False
        for hyp in hypotheses:
            self.assertIn("title", hyp)
            self.assertIn("description", hyp)
            self.assertIn("lesson_id", hyp)
            self.assertIn("commit", hyp)

            if hyp["title"] == self.unique_title:
                found = True
                self.assertIn(self.unique_content, hyp["description"] or "")
                self.assertTrue(len(hyp["commit"]) >= 7)

        self.assertTrue(found, "Сгенерированная гипотеза для созданного урока не найдена.")

    def test_analyze_repository_context_integration(self):
        history = self.git_inspector.get_commit_history(max_count=1)
        self.assertGreater(len(history), 0)
        commit_hash = history[0].get("commit") or history[0].get("hash") or history[0].get("id")

        if not commit_hash:
            res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo_path, capture_output=True, text=True, check=True)
            commit_hash = res.stdout.strip()

        context = self.hypothesis_generator._analyze_repository_context(commit_hash, self.file_name)

        self.assertIsInstance(context, dict)
        self.assertIn("diff", context)
        self.assertIn("file_content", context)
        self.assertIn(self.unique_content, context["file_content"])


if __name__ == "__main__":
    unittest.main()