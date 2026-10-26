import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import os
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

class TestPatchVerifierModule(unittest.TestCase):

    def setUp(self):
        self.rand_repo = f"/repo_{uuid.uuid4().hex[:8]}"
        self.rand_commit = uuid.uuid4().hex
        self.rand_author = f"Author_{uuid.uuid4().hex[:6]}"
        self.rand_message = f"Msg_{uuid.uuid4().hex[:6]}"
        self.rand_file = f"src/{uuid.uuid4().hex[:6]}.py"
        self.rand_content = f"print('{uuid.uuid4().hex[:8]}')"

    def test_git_inspector_run_git(self):
        inspector = GitInspector(self.rand_repo)
        rand_output = f"{uuid.uuid4().hex}\n"
        with patch("subprocess.run") as mock_run:
            mock_res = MagicMock()
            mock_res.stdout = rand_output
            mock_run.return_value = mock_res
            
            res = inspector._run_git(["status"])
            self.assertEqual(res, rand_output.strip())
            mock_run.assert_called_once()

    def test_git_inspector_get_commit_history(self):
        inspector = GitInspector(self.rand_repo)
        log_line = f"{self.rand_commit}|{self.rand_author}|{self.rand_message}"
        with patch.object(inspector, "_run_git", return_value=log_line) as mock_run:
            history = inspector.get_commit_history(max_count=random.randint(1, 15))
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["hash"], self.rand_commit)
            self.assertEqual(history[0]["author"], self.rand_author)
            self.assertEqual(history[0]["message"], self.rand_message)
            mock_run.assert_called_once()

    def test_git_inspector_get_commit_history_empty(self):
        inspector = GitInspector(self.rand_repo)
        with patch.object(inspector, "_run_git", return_value="") as mock_run:
            history = inspector.get_commit_history()
            self.assertEqual(history, [])

    def test_git_inspector_get_file_diff(self):
        inspector = GitInspector(self.rand_repo)
        diff_text = f"diff --git a/{self.rand_file} b/{self.rand_file}"
        with patch.object(inspector, "_run_git", return_value=diff_text) as mock_run:
            res = inspector.get_file_diff(self.rand_commit)
            self.assertEqual(res, diff_text)
            mock_run.assert_called_with(["show", self.rand_commit])

    def test_git_inspector_analyze_repository(self):
        inspector = GitInspector(self.rand_repo)
        commit_data = {"hash": self.rand_commit, "author": self.rand_author, "message": self.rand_message}
        with patch.object(inspector, "get_commit_history", return_value=[commit_data]):
            analysis = inspector.analyze_repository()
            self.assertEqual(analysis["total_commits"], 1)
            self.assertEqual(analysis["latest_commit"], commit_data)

    def test_git_inspector_read_file_at_commit(self):
        inspector = GitInspector(self.rand_repo)
        with patch.object(inspector, "_run_git", return_value=self.rand_content) as mock_run:
            res = inspector.read_file_at_commit(self.rand_commit, self.rand_file)
            self.assertEqual(res, self.rand_content)
            mock_run.assert_called_with(["show", f"{self.rand_commit}:{self.rand_file}"])

    def test_git_inspector_get_history_and_latest_changes(self):
        inspector = GitInspector(self.rand_repo)
        commit_data = {"hash": self.rand_commit, "author": self.rand_author, "message": self.rand_message}
        with patch.object(inspector, "get_commit_history", return_value=[commit_data]) as mock_hist, \
             patch.object(inspector, "get_file_diff", return_value=self.rand_content) as mock_diff:

            hist = inspector.get_history(max_count=5)
            self.assertEqual(hist, [commit_data])
            mock_hist.assert_called_with(5)

            latest = inspector.get_latest_changes()
            self.assertEqual(latest, self.rand_content)
            mock_diff.assert_called_with(self.rand_commit)

    def test_lesson_parser(self):
        inspector = GitInspector(self.rand_repo)
        parser = LessonParser(inspector)
        lessons = parser.parse_lessons()
        self.assertIsInstance(lessons, list)
        self.assertTrue(len(lessons) > 0)

        extracted = parser.extract_lessons(max_commits=random.randint(1, 20))
        self.assertIn("lesson_id", extracted)
        self.assertIn("content", extracted)

    def test_hypothesis_generator(self):
        inspector = GitInspector(self.rand_repo)
        parser = LessonParser(inspector)
        generator = HypothesisGenerator(inspector, parser)

        hyps = generator.generate_hypotheses()
        self.assertIsInstance(hyps, list)
        
        rand_id_1 = uuid.uuid4().hex
        rand_id_2 = uuid.uuid4().hex
        unsorted = [
            {"id": rand_id_1, "weight": random.uniform(0.1, 0.4)},
            {"id": rand_id_2, "weight": random.uniform(0.6, 0.9)}
        ]
        prioritized = generator.prioritize_hypotheses(unsorted)
        self.assertEqual(prioritized[0]["id"], rand_id_2)

    def test_patch_executor_apply_success(self):
        inspector = GitInspector(self.rand_repo)
        parser = LessonParser(inspector)
        executor = PatchExecutor(self.rand_repo, inspector, parser)

        patch_data = {
            "file_path": self.rand_file,
            "content": self.rand_content,
            "commit_message": self.rand_message
        }

        with patch("builtins.open", unittest.mock.mock_open()), \
             patch("os.makedirs") as mock_dirs, \
             patch("subprocess.run") as mock_sub:
            
            res = executor.apply_patch(patch_data)
            self.assertTrue(res)
            mock_dirs.assert_called_once()
            self.assertEqual(mock_sub.call_count, 2)

    def test_patch_executor_apply_missing_data(self):
        inspector = GitInspector(self.rand_repo)
        parser = LessonParser(inspector)
        executor = PatchExecutor(self.rand_repo, inspector, parser)

        self.assertFalse(executor.apply_patch({"file_path": self.rand_file}))
        self.assertFalse(executor.apply_patch({"content": self.rand_content}))

    def test_patch_executor_apply_exception(self):
        inspector = GitInspector(self.rand_repo)
        parser = LessonParser(inspector)
        executor = PatchExecutor(self.rand_repo, inspector, parser)

        patch_data = {
            "file_path": self.rand_file,
            "content": self.rand_content
        }

        with patch("builtins.open", side_effect=Exception("Disk full")):
            res = executor.apply_patch(patch_data)
            self.assertFalse(res)

    def test_patch_executor_rollback_success(self):
        inspector = GitInspector(self.rand_repo)
        parser = LessonParser(inspector)
        executor = PatchExecutor(self.rand_repo, inspector, parser)

        with patch("subprocess.run") as mock_sub:
            res = executor.rollback_patch(self.rand_file, self.rand_commit)
            self.assertTrue(res)
            mock_sub.assert_called_once()

    def test_patch_executor_rollback_exception(self):
        inspector = GitInspector(self.rand_repo)
        parser = LessonParser(inspector)
        executor = PatchExecutor(self.rand_repo, inspector, parser)

        with patch("subprocess.run", side_effect=Exception("Git error")):
            res = executor.rollback_patch(self.rand_file, self.rand_commit)
            self.assertFalse(res)

    def test_patch_executor_execute_from_lessons(self):
        inspector = GitInspector(self.rand_repo)
        parser = LessonParser(inspector)
        executor = PatchExecutor(self.rand_repo, inspector, parser)
        res = executor.execute_from_lessons()
        self.assertIn("executed_lessons", res)
        self.assertEqual(res["status"], "success")

    def test_patch_verifier_verify_and_apply_syntax_error(self):
        inspector = GitInspector(self.rand_repo)
        executor = PatchExecutor(self.rand_repo, inspector, LessonParser(inspector))
        verifier = PatchVerifier(self.rand_repo, inspector, executor)

        bad_content = f"code = 1\nsyntax error here\n{uuid.uuid4().hex}"
        patch_data = {
            "file_path": self.rand_file,
            "content": bad_content
        }

        res = verifier.verify_and_apply(patch_data)
        self.assertFalse(res)

    def test_patch_verifier_verify_and_apply_success(self):
        inspector = GitInspector(self.rand_repo)
        executor = PatchExecutor(self.rand_repo, inspector, LessonParser(inspector))
        verifier = PatchVerifier(self.rand_repo, inspector, executor)

        patch_data = {
            "file_path": self.rand_file,
            "content": self.rand_content
        }

        with patch.object(executor, "apply_patch", return_value=True) as mock_apply:
            res = verifier.verify_and_apply(patch_data)
            self.assertTrue(res)
            mock_apply.assert_called_once_with(patch_data)