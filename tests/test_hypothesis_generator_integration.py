import os
import subprocess
import tempfile
import unittest
import uuid
from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser
from skills.hypothesis_generator import HypothesisGenerator


class TestHypothesisGeneratorIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name

        subprocess.run(["git", "init"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "IntegrationTester"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "integration@test.local"], cwd=self.repo_path, check=True, capture_output=True)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_generate_hypotheses_from_real_git_and_lessons(self):
        token_lesson = f"lesson_{uuid.uuid4().hex}"
        token_feature = f"feature_{uuid.uuid4().hex}"

        lesson_file_path = os.path.join(self.repo_path, "LESSONS.md")
        lesson_text = (
            f"# Repository Lessons\n\n"
            f"- Lesson: Component {token_lesson} requires automated cache invalidation.\n"
        )
        with open(lesson_file_path, "w", encoding="utf-8") as f:
            f.write(lesson_text)

        subprocess.run(["git", "add", "LESSONS.md"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"docs: register lesson for {token_lesson}"],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )

        source_file_path = os.path.join(self.repo_path, f"{token_feature}.py")
        with open(source_file_path, "w", encoding="utf-8") as f:
            f.write(f"def process_{token_feature}():\n    return '{token_feature}'\n")

        subprocess.run(["git", "add", f"{token_feature}.py"], cwd=self.repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"feat: implement {token_feature}"],
            cwd=self.repo_path,
            check=True,
            capture_output=True,
        )

        git_inspector = GitInspector(self.repo_path)
        lesson_parser = LessonParser(git_inspector)
        generator = HypothesisGenerator(git_inspector=git_inspector, lesson_parser=lesson_parser)

        hypotheses = generator.generate_hypotheses()

        self.assertIsInstance(hypotheses, list)
        self.assertGreater(len(hypotheses), 0, "Hypothesis generator must return at least one hypothesis")

        serialized_hypotheses = str(hypotheses)
        self.assertTrue(
            token_lesson in serialized_hypotheses or token_feature in serialized_hypotheses,
            f"Expected either lesson token '{token_lesson}' or feature token '{token_feature}' "
            f"in generated hypotheses: {serialized_hypotheses}",
        )


if __name__ == "__main__":
    unittest.main()