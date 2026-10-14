import unittest
import uuid
import random
import os
import tempfile
import git
from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser
from skills.hypothesis_generator import HypothesisGenerator


class TestHypothesisGeneratorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.repo = git.Repo.init(self.repo_path)

        self.repo.git.config('user.name', 'Architect Test')
        self.repo.git.config('user.email', 'architect@test.com')

        self.random_title = f"Lesson_{uuid.uuid4().hex[:8]}"
        self.random_insight = f"Insight_{uuid.uuid4().hex[:8]}"
        self.random_metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        self.random_metric_val = random.randint(10, 100)

        file_content = f"# {self.random_title}\n# insight: {self.random_insight}\n{self.random_metric_name} = {self.random_metric_val}\n"
        self.file_name = "lesson.md"
        self.file_path = os.path.join(self.repo_path, self.file_name)

        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write(file_content)

        self.repo.index.add([self.file_name])
        self.commit = self.repo.index.commit(f"Add {self.random_title}")
        self.commit_hash = self.commit.hexsha[:7]

        self.git_inspector = GitInspector(repo_path=self.repo_path)
        self.lesson_parser = LessonParser(git_inspector=self.git_inspector)
        self.generator = HypothesisGenerator(git_inspector=self.git_inspector, lesson_parser=self.lesson_parser)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_generate_hypotheses_and_snapshot(self):
        max_commits = random.randint(1, 15)
        hypotheses = self.generator.generate_hypotheses(max_commits=max_commits)

        self.assertIsInstance(hypotheses, list)
        self.assertTrue(len(hypotheses) > 0)

        found = False
        for h in hypotheses:
            if h.get("title") == self.random_title:
                found = True
                self.assertEqual(h.get("insight"), self.random_insight)
                self.assertIn(self.random_title, h.get("hypothesis"))
                self.assertIn(self.random_insight, h.get("hypothesis"))
                self.assertIn(self.commit_hash, h.get("hypothesis"))

        self.assertTrue(found, f"Сгенерированный урок с заголовком '{self.random_title}' не найден через реальные зависимости.")

        snapshot_content = self.generator.analyze_file_snapshot(self.commit_hash, self.file_name)
        self.assertIn(self.random_title, snapshot_content)
        self.assertIn(self.random_insight, snapshot_content)

        diff_data = self.git_inspector.get_file_diff(self.commit_hash)
        metrics = self.generator._extract_metrics_from_diff(diff_data)
        self.assertIn(self.random_metric_name, metrics)
        self.assertEqual(metrics[self.random_metric_name], self.random_metric_val)


if __name__ == "__main__":
    unittest.main()