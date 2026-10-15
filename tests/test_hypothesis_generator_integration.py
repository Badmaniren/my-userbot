import unittest
import uuid
import random
import tempfile
import os
import subprocess
from skills.hypothesis_generator import HypothesisGenerator, HypothesisGeneratorError
from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser


class TestHypothesisGeneratorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name

        subprocess.run(["git", "init"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "Architect Test"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "architect@test.com"], cwd=self.repo_path, check=True, capture_output=True)

        self.random_id = str(uuid.uuid4())
        self.lesson_title = f"Lesson {self.random_id}"
        self.commit_message = f"Commit {self.random_id}"

        lesson_filename = f"lesson_{uuid.uuid4().hex[:8]}.txt"
        self.lesson_filepath = os.path.join(self.repo_path, lesson_filename)

        lesson_content = f"ID: {self.random_id}\nTitle: {self.lesson_title}\nContent: Real integration test content."
        with open(self.lesson_filepath, "w", encoding="utf-8") as f:
            f.write(lesson_content)

        subprocess.run(["git", "add", lesson_filename], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", self.commit_message], cwd=self.repo_path, check=True, capture_output=True)

        self.generator = HypothesisGenerator(repo_path=self.repo_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_generate_hypotheses_integration(self):
        max_commits = random.randint(5, 15)
        hypotheses = self.generator.generate_hypotheses(max_commits=max_commits)

        self.assertIsInstance(hypotheses, list)
        self.assertGreaterEqual(len(hypotheses), 1)

        found_lesson_hypothesis = False
        found_commit_hypothesis = False

        for h in hypotheses:
            self.assertIn("priority_score", h)
            if h.get("priority_score") == 10:
                if h.get("id") == self.random_id or self.random_id in str(h.get("content", "")):
                    found_lesson_hypothesis = True
            elif h.get("priority_score") == 5:
                if h.get("title") == self.commit_message:
                    found_commit_hypothesis = True

        self.assertTrue(found_lesson_hypothesis, "Синтезированная гипотеза из урока не найдена в реальном репозитории")
        self.assertTrue(found_commit_hypothesis, "Синтезированная гипотеза из коммита не найдена в реальном репозитории")

    def test_prioritize_hypotheses_integration(self):
        dummy_hypotheses = [
            {"id": str(uuid.uuid4()), "title": "Low priority", "priority_score": random.randint(1, 3)},
            {"id": str(uuid.uuid4()), "title": "High priority", "priority_score": random.randint(8, 10)},
            {"id": str(uuid.uuid4()), "title": "Medium priority", "priority_score": random.randint(4, 7)}
        ]

        prioritized = self.generator.prioritize_hypotheses(dummy_hypotheses)

        self.assertEqual(len(prioritized), 3)
        self.assertGreaterEqual(prioritized[0]["priority_score"], prioritized[1]["priority_score"])
        self.assertGreaterEqual(prioritized[1]["priority_score"], prioritized[2]["priority_score"])

    def test_analyze_trends_integration(self):
        random_data = uuid.uuid4().bytes + os.urandom(16)
        temp_file = os.path.join(self.repo_path, f"trend_{uuid.uuid4().hex}.bin")

        with open(temp_file, "wb") as f:
            f.write(random_data)

        read_data = self.generator.analyze_trends(temp_file)
        self.assertEqual(read_data, random_data)


if __name__ == "__main__":
    unittest.main()