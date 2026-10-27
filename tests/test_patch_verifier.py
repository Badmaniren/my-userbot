import unittest
import os
import shutil
import tempfile
import uuid
import random
import subprocess
from unittest.mock import patch, MagicMock
import io

from skills.patch_verifier import (
    HypothesisGeneratorError,
    LessonParserError,
    PatchExecutorError,
    GitInspector,
    LessonParser,
    HypothesisGenerator,
    PatchExecutor,
    PatchVerifier
)

class TestPatchVerifierIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir
        subprocess.run(["git", "-C", self.test_dir, "init"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Inquisitor"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "inquisitor@architecture.void"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_full_patch_pipeline_integration(self):
        file_name = f"{uuid.uuid4().hex}.py"
        file_content = f"print('{uuid.uuid4().hex}')\n"
        commit_msg = f"Commit {uuid.uuid4().hex}"

        inspector = GitInspector(self.repo_path)
        parser = LessonParser(inspector)
        executor = PatchExecutor(self.repo_path, inspector, parser)
        verifier = PatchVerifier(self.repo_path, inspector, executor)

        patch_data = {
            "file_path": file_name,
            "content": file_content,
            "commit_message": commit_msg
        }

        res = verifier.verify_and_apply(patch_data)
        self.assertTrue(res)

        history = inspector.get_commit_history(max_count=1)
        self.assertTrue(len(history) > 0)
        self.assertEqual(history[0]["message"], commit_msg)

    def test_syntax_error_patch_rejection(self):
        file_name = f"{uuid.uuid4().hex}.py"
        file_content = f"syntax error here: {uuid.uuid4().hex}"

        inspector = GitInspector(self.repo_path)
        parser = LessonParser(inspector)
        executor = PatchExecutor(self.repo_path, inspector, parser)
        verifier = PatchVerifier(self.repo_path, inspector, executor)

        patch_data = {
            "file_path": file_name,
            "content": file_content,
            "commit_message": "Bad syntax commit"
        }

        res = verifier.verify_and_apply(patch_data)
        self.assertFalse(res)

        history = inspector.get_commit_history(max_count=1)
        self.assertEqual(len(history), 0)


class TestGitInspector(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "-C", self.test_dir, "init"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Tester"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "tester@test.com"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_analyze_repository_and_history(self):
        inspector = GitInspector(self.test_dir)
        analysis = inspector.analyze_repository()
        self.assertEqual(analysis["total_commits"], 0)
        self.assertIsNone(analysis["latest_commit"])

        file_name = f"{uuid.uuid4().hex}.txt"
        file_path = os.path.join(self.test_dir, file_name)
        file_content = uuid.uuid4().hex
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(file_content)

        subprocess.run(["git", "-C", self.test_dir, "add", file_name], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        msg = f"msg_{uuid.uuid4().hex}"
        subprocess.run(["git", "-C", self.test_dir, "commit", "-m", msg], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        history = inspector.get_commit_history(max_count=5)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["message"], msg)

        read_content = inspector.read_file_at_commit(history[0]["hash"], file_name)
        self.assertEqual(read_content, file_content)

        diff = inspector.get_file_diff(history[0]["hash"])
        self.assertIn(file_name, diff)

        latest = inspector.get_latest_changes()
        self.assertIn(file_name, latest)


class TestLessonParserAndHypothesis(unittest.TestCase):
    def test_lesson_parser_and_hypothesis(self):
        random_repo = uuid.uuid4().hex
        inspector = GitInspector(random_repo)
        parser = LessonParser(inspector)
        lessons = parser.parse_lessons()
        self.assertIsInstance(lessons, list)
        extracted = parser.extract_lessons()
        self.assertIsInstance(extracted, dict)

        generator = HypothesisGenerator(inspector, parser)
        hypotheses = generator.generate_hypotheses()
        self.assertIsInstance(hypotheses, list)

        weighted_hypotheses = [
            {"id": uuid.uuid4().hex, "weight": random.random()},
            {"id": uuid.uuid4().hex, "weight": random.random() + 1.0}
        ]
        prioritized = generator.prioritize_hypotheses(weighted_hypotheses)
        self.assertGreaterEqual(prioritized[0]["weight"], prioritized[1]["weight"])


class TestPatchExecutorAndVerifier(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        subprocess.run(["git", "-C", self.test_dir, "init"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.name", "Executor"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "-C", self.test_dir, "config", "user.email", "exec@test.com"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_patch_executor_apply_and_rollback(self):
        inspector = GitInspector(self.test_dir)
        parser = LessonParser(inspector)
        executor = PatchExecutor(self.test_dir, inspector, parser)

        file_name = f"{uuid.uuid4().hex}.py"
        content_v1 = f"val = {random.randint(1, 100)}"
        content_v2 = f"val = {random.randint(101, 200)}"

        patch_1 = {"file_path": file_name, "content": content_v1, "commit_message": "v1"}
        res1 = executor.apply_patch(patch_1)
        self.assertTrue(res1)

        history = inspector.get_commit_history(max_count=1)
        commit_hash_1 = history[0]["hash"]

        patch_2 = {"file_path": file_name, "content": content_v2, "commit_message": "v2"}
        res2 = executor.apply_patch(patch_2)
        self.assertTrue(res2)

        full_path = os.path.join(self.test_dir, file_name)
        with open(full_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), content_v2)

        rolled = executor.rollback_patch(file_name, commit_hash_1)
        self.assertTrue(rolled)

        with open(full_path, "r", encoding="utf-8") as f:
            self.assertEqual(f.read(), content_v1)

        exec_lessons = executor.execute_from_lessons()
        self.assertIn("status", exec_lessons)

    def test_patch_executor_failures(self):
        inspector = GitInspector(self.test_dir)
        parser = LessonParser(inspector)
        executor = PatchExecutor(self.test_dir, inspector, parser)

        bad_patch = {"content": uuid.uuid4().hex}
        self.assertFalse(executor.apply_patch(bad_patch))

        with patch("subprocess.run", side_effect=Exception("Git subprocess error")):
            res = executor.rollback_patch(uuid.uuid4().hex, uuid.uuid4().hex)
            self.assertFalse(res)


if __name__ == "__main__":
    unittest.main()