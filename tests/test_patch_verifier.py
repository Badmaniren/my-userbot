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
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.inspector = GitInspector(self.repo_path)
        self.parser = LessonParser(self.inspector)
        self.generator = HypothesisGenerator(self.inspector, self.parser)
        self.executor = PatchExecutor(self.repo_path, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.repo_path, self.inspector, self.executor)

    def test_git_inspector_run_git(self):
        cmd_arg = uuid.uuid4().hex
        mock_result = MagicMock()
        mock_result.stdout = f"commit_{uuid.uuid4().hex}"

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            res = self.inspector._run_git([cmd_arg])
            self.assertEqual(res, mock_result.stdout.strip())
            mock_run.assert_called_once()

    def test_git_inspector_get_commit_history_empty(self):
        with patch.object(self.inspector, "_run_git", return_value=""):
            history = self.inspector.get_commit_history(max_count=random.randint(1, 10))
            self.assertEqual(history, [])

    def test_git_inspector_get_commit_history_valid(self):
        h_hash = uuid.uuid4().hex
        author = uuid.uuid4().hex
        msg = uuid.uuid4().hex
        raw_output = f"{h_hash}|{author}|{msg}"

        with patch.object(self.inspector, "_run_git", return_value=raw_output):
            history = self.inspector.get_commit_history(max_count=1)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["hash"], h_hash)
            self.assertEqual(history[0]["author"], author)
            self.assertEqual(history[0]["message"], msg)

    def test_git_inspector_analyze_repository(self):
        h_hash = uuid.uuid4().hex
        author = uuid.uuid4().hex
        msg = uuid.uuid4().hex
        raw_output = f"{h_hash}|{author}|{msg}"

        with patch.object(self.inspector, "_run_git", return_value=raw_output):
            analysis = self.inspector.analyze_repository()
            self.assertEqual(analysis["total_commits"], 1)
            self.assertEqual(analysis["latest_commit"]["hash"], h_hash)

    def test_git_inspector_read_file_at_commit(self):
        c_hash = uuid.uuid4().hex
        f_path = f"{uuid.uuid4().hex}.py"
        expected_content = uuid.uuid4().hex

        with patch.object(self.inspector, "_run_git", return_value=expected_content) as mock_run:
            content = self.inspector.read_file_at_commit(c_hash, f_path)
            self.assertEqual(content, expected_content)
            mock_run.assert_called_once_with(["show", f"{c_hash}:{f_path}"])

    def test_git_inspector_get_history_and_latest(self):
        h_hash = uuid.uuid4().hex
        author = uuid.uuid4().hex
        msg = uuid.uuid4().hex
        raw_output = f"{h_hash}|{author}|{msg}"
        diff_content = uuid.uuid4().hex

        with patch.object(self.inspector, "_run_git", side_effect=[raw_output, diff_content]):
            latest = self.inspector.get_latest_changes()
            self.assertEqual(latest, diff_content)

        with patch.object(self.inspector, "get_commit_history", return_value=[{"hash": h_hash, "author": author, "message": msg}]) as mock_gc:
            hist = self.inspector.get_history(max_count=5)
            self.assertEqual(len(hist), 1)
            mock_gc.assert_called_once_with(5)

    def test_lesson_parser(self):
        lessons = self.parser.parse_lessons()
        self.assertIsInstance(lessons, list)
        self.assertTrue(len(lessons) > 0)

        extracted = self.parser.extract_lessons(max_commits=random.randint(1, 20))
        self.assertIsInstance(extracted, dict)
        self.assertIn("lesson_id", extracted)

    def test_hypothesis_generator(self):
        hypotheses = self.generator.generate_hypotheses(max_commits=random.randint(1, 10))
        self.assertIsInstance(hypotheses, list)

        h1_weight = random.random()
        h2_weight = h1_weight + random.uniform(0.1, 0.5)
        unsorted = [
            {"id": uuid.uuid4().hex, "weight": h1_weight},
            {"id": uuid.uuid4().hex, "weight": h2_weight}
        ]
        prioritized = self.generator.prioritize_hypotheses(unsorted)
        self.assertEqual(prioritized[0]["weight"], h2_weight)

    def test_patch_executor_apply_patch_invalid(self):
        patch_data = {"content": uuid.uuid4().hex} # missing file_path
        res = self.executor.apply_patch(patch_data)
        self.assertFalse(res)

    def test_patch_executor_apply_patch_success(self):
        file_path = f"{uuid.uuid4().hex}.py"
        content = uuid.uuid4().hex
        commit_msg = uuid.uuid4().hex
        patch_data = {
            "file_path": file_path,
            "content": content,
            "commit_message": commit_msg
        }

        mock_file = MagicMock()
        with patch("builtins.open", return_value=mock_file) as mock_open, \
             patch("os.makedirs") as mock_mkdirs, \
             patch("subprocess.run") as mock_subproc:
            
            res = self.executor.apply_patch(patch_data)
            self.assertTrue(res)
            mock_mkdirs.assert_called_once()
            mock_open.assert_called_once()
            self.assertEqual(mock_subproc.call_count, 2)

    def test_patch_executor_rollback_patch(self):
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex

        with patch("subprocess.run") as mock_subproc:
            res = self.executor.rollback_patch(file_path, commit_hash)
            self.assertTrue(res)
            mock_subproc.assert_called_once()

    def test_patch_executor_rollback_patch_exception(self):
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex

        with patch("subprocess.run", side_effect=Exception("git error")):
            res = self.executor.rollback_patch(file_path, commit_hash)
            self.assertFalse(res)

    def test_patch_executor_execute_from_lessons(self):
        res = self.executor.execute_from_lessons()
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("status"), "success")

    def test_patch_verifier_syntax_error(self):
        bad_content = f"print({uuid.uuid4().hex}); syntax error here"
        patch_data = {"content": bad_content}
        res = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(res)

    def test_patch_verifier_success(self):
        good_content = f"print('{uuid.uuid4().hex}')"
        patch_data = {"content": good_content, "file_path": f"{uuid.uuid4().hex}.py"}

        with patch.object(self.executor, "apply_patch", return_value=True) as mock_apply:
            res = self.verifier.verify_and_apply(patch_data)
            self.assertTrue(res)
            mock_apply.assert_called_once_with(patch_data)