import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import os

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

class TestPatchVerifierModule(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/tmp/repo_{uuid.uuid4().hex[:8]}"
        self.rand_file = f"src_{uuid.uuid4().hex[:6]}.py"
        self.rand_commit = uuid.uuid4().hex
        self.rand_author = f"Author_{uuid.uuid4().hex[:4]}"
        self.rand_msg = f"Commit msg {uuid.uuid4().hex[:6]}"

    def test_git_inspector_get_commit_history(self):
        inspector = GitInspector(self.rand_repo)
        mock_output = f"{self.rand_commit}|{self.rand_author}|{self.rand_msg}\n"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = mock_output
            history = inspector.get_commit_history(max_count=5)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["hash"], self.rand_commit)
            self.assertEqual(history[0]["author"], self.rand_author)
            self.assertEqual(history[0]["message"], self.rand_msg)

    def test_git_inspector_get_file_diff(self):
        inspector = GitInspector(self.rand_repo)
        expected_diff = f"diff --git a/{self.rand_file} b/{self.rand_file}\n+random_addition_{uuid.uuid4().hex[:4]}"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = expected_diff
            diff = inspector.get_file_diff(self.rand_commit)
            self.assertEqual(diff, expected_diff)

    def test_git_inspector_analyze_repository(self):
        inspector = GitInspector(self.rand_repo)
        mock_output = f"{self.rand_commit}|{self.rand_author}|{self.rand_msg}"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = mock_output
            analysis = inspector.analyze_repository()
            self.assertEqual(analysis["total_commits"], 1)
            self.assertEqual(analysis["latest_commit"]["hash"], self.rand_commit)

    def test_git_inspector_read_file_at_commit(self):
        inspector = GitInspector(self.rand_repo)
        file_content = f"print('{uuid.uuid4().hex}')"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = file_content
            res = inspector.read_file_at_commit(self.rand_commit, self.rand_file)
            self.assertEqual(res, file_content)

    def test_git_inspector_aliases(self):
        inspector = GitInspector(self.rand_repo)
        mock_output = f"{self.rand_commit}|{self.rand_author}|{self.rand_msg}"
        with patch("subprocess.run") as mock_run:
            mock_run.return_value.stdout = mock_output
            history = inspector.get_history(max_count=3)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["hash"], self.rand_commit)

            diff_output = f"diff {uuid.uuid4().hex}"
            mock_run.return_value.stdout = diff_output
            latest_diff = inspector.get_latest_changes()
            self.assertEqual(latest_diff, diff_output)

    def test_lesson_parser_methods(self):
        inspector = MagicMock(spec=GitInspector)
        parser = LessonParser(inspector)
        lessons = parser.parse_lessons()
        self.assertIsInstance(lessons, list)
        self.assertTrue(len(lessons) > 0)

        extracted = parser.extract_lessons(max_commits=random.randint(1, 20))
        self.assertIsInstance(extracted, dict)
        self.assertIn("lesson_id", extracted)

    def test_hypothesis_generator_methods(self):
        inspector = MagicMock(spec=GitInspector)
        parser = MagicMock(spec=LessonParser)
        generator = HypothesisGenerator(inspector, parser)

        hypotheses = generator.generate_hypotheses()
        self.assertIsInstance(hypotheses, list)

        rand_weight_1 = random.random()
        rand_weight_2 = random.random() + 1.0
        input_hyps = [
            {"id": uuid.uuid4().hex, "weight": rand_weight_1},
            {"id": uuid.uuid4().hex, "weight": rand_weight_2}
        ]
        prioritized = generator.prioritize_hypotheses(input_hyps)
        self.assertEqual(prioritized[0]["weight"], rand_weight_2)

    def test_patch_executor_apply_and_rollback(self):
        inspector = MagicMock(spec=GitInspector)
        parser = MagicMock(spec=LessonParser)
        executor = PatchExecutor(self.rand_repo, inspector, parser)

        patch_data = {
            "file_path": self.rand_file,
            "content": f"content_{uuid.uuid4().hex}",
            "commit_message": self.rand_msg
        }

        with patch("builtins.open", new_callable=unittest.mock.mock_open()) as mock_file, \
             patch("os.makedirs") as mock_mkdirs, \
             patch("subprocess.run") as mock_run:

            success = executor.apply_patch(patch_data)
            self.assertTrue(success)
            mock_mkdirs.assert_called_once()
            mock_file.assert_called_once()
            self.assertEqual(mock_run.call_count, 2)

        with patch("subprocess.run") as mock_run:
            rb_success = executor.rollback_patch(self.rand_file, self.rand_commit)
            self.assertTrue(rb_success)
            mock_run.assert_called_once()

        exec_lessons = executor.execute_from_lessons()
        self.assertIsInstance(exec_lessons, dict)
        self.assertIn("status", exec_lessons)

    def test_patch_executor_apply_patch_failure(self):
        inspector = MagicMock(spec=GitInspector)
        parser = MagicMock(spec=LessonParser)
        executor = PatchExecutor(self.rand_repo, inspector, parser)

        bad_patch_data = {"file_path": "", "content": None}
        success = executor.apply_patch(bad_patch_data)
        self.assertFalse(success)

        patch_data = {
            "file_path": self.rand_file,
            "content": f"content_{uuid.uuid4().hex}"
        }
        with patch("builtins.open", side_effect=Exception("Disk full")):
            success_exc = executor.apply_patch(patch_data)
            self.assertFalse(success_exc)

    def test_patch_verifier_verify_and_apply(self):
        inspector = MagicMock(spec=GitInspector)
        executor = MagicMock(spec=PatchExecutor)
        verifier = PatchVerifier(self.rand_repo, inspector, executor)

        erroneous_content = f"print('hello'); syntax error here; {uuid.uuid4().hex}"
        bad_patch = {"content": erroneous_content, "file_path": self.rand_file}

        res_bad = verifier.verify_and_apply(bad_patch)
        self.assertFalse(res_bad)
        executor.apply_patch.assert_not_called()

        valid_content = f"print('{uuid.uuid4().hex}')"
        good_patch = {"content": valid_content, "file_path": self.rand_file}
        executor.apply_patch.return_value = True

        res_good = verifier.verify_and_apply(good_patch)
        self.assertTrue(res_good)
        executor.apply_patch.assert_called_once_with(good_patch)

if __name__ == "__main__":
    unittest.main()