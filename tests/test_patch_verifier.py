import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import os
import subprocess

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
        self.executor = PatchExecutor(self.repo_path, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.repo_path, self.inspector, self.executor)

    @patch("subprocess.run")
    def test_git_inspector_run_git(self, mock_subprocess):
        expected_output = uuid.uuid4().hex
        mock_process = MagicMock()
        mock_process.stdout = f"{expected_output}\n"
        mock_subprocess.return_value = mock_process

        random_arg = uuid.uuid4().hex
        result = self.inspector._run_git([random_arg])

        self.assertEqual(result, expected_output)
        mock_subprocess.assert_called_once_with(
            ["git", "-C", self.repo_path, random_arg],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )

    @patch("skills.patch_verifier.GitInspector._run_git")
    def test_git_inspector_get_commit_history(self, mock_run_git):
        commit_hash = uuid.uuid4().hex
        author = uuid.uuid4().hex
        message = uuid.uuid4().hex
        mock_run_git.return_value = f"{commit_hash}|{author}|{message}"

        max_count = random.randint(1, 50)
        history = self.inspector.get_commit_history(max_count=max_count)

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["hash"], commit_hash)
        self.assertEqual(history[0]["author"], author)
        self.assertEqual(history[0]["message"], message)
        mock_run_git.assert_called_once_with(["log", f"-n {max_count}", "--pretty=format:%H|%an|%s"])

    @patch("skills.patch_verifier.GitInspector._run_git")
    def test_git_inspector_get_file_diff(self, mock_run_git):
        diff_content = uuid.uuid4().hex
        mock_run_git.return_value = diff_content

        commit_hash = uuid.uuid4().hex
        result = self.inspector.get_file_diff(commit_hash)

        self.assertEqual(result, diff_content)
        mock_run_git.assert_called_once_with(["show", commit_hash])

    @patch("skills.patch_verifier.GitInspector.get_commit_history")
    def test_git_inspector_analyze_repository(self, mock_get_history):
        commit_hash = uuid.uuid4().hex
        mock_get_history.return_value = [{"hash": commit_hash, "author": "dev", "message": "msg"}]

        analysis = self.inspector.analyze_repository()

        self.assertEqual(analysis["total_commits"], 1)
        self.assertEqual(analysis["latest_commit"]["hash"], commit_hash)

    @patch("skills.patch_verifier.GitInspector._run_git")
    def test_git_inspector_read_file_at_commit(self, mock_run_git):
        file_content = uuid.uuid4().hex
        mock_run_git.return_value = file_content

        commit_hash = uuid.uuid4().hex
        file_path = f"{uuid.uuid4().hex}.py"
        result = self.inspector.read_file_at_commit(commit_hash, file_path)

        self.assertEqual(result, file_content)
        mock_run_git.assert_called_once_with(["show", f"{commit_hash}:{file_path}"])

    def test_lesson_parser_methods(self):
        lessons = self.parser.parse_lessons()
        self.assertIsInstance(lessons, list)
        extracted = self.parser.extract_lessons()
        self.assertIsInstance(extracted, dict)

    def test_hypothesis_generator_prioritize(self):
        generator = HypothesisGenerator(self.inspector, self.parser)
        hypotheses = generator.generate_hypotheses()
        self.assertIsInstance(hypotheses, list)

        prioritized = generator.prioritize_hypotheses([
            {"id": uuid.uuid4().hex, "weight": 0.2},
            {"id": uuid.uuid4().hex, "weight": 0.9}
        ])
        self.assertEqual(prioritized[0]["weight"], 0.9)

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    @patch("os.makedirs")
    def test_patch_executor_apply_patch_success(self, mock_makedirs, mock_open, mock_subprocess):
        file_path = f"{uuid.uuid4().hex}.py"
        content = uuid.uuid4().hex
        commit_message = uuid.uuid4().hex
        patch_data = {
            "file_path": file_path,
            "content": content,
            "commit_message": commit_message
        }

        result = self.executor.apply_patch(patch_data)

        self.assertTrue(result)
        mock_makedirs.assert_called_once()
        mock_open.assert_called_once()
        self.assertEqual(mock_subprocess.call_count, 2)

    def test_patch_executor_apply_patch_invalid_data(self):
        patch_data = {"file_path": "", "content": None}
        result = self.executor.apply_patch(patch_data)
        self.assertFalse(result)

    @patch("subprocess.run")
    def test_patch_executor_rollback_patch(self, mock_subprocess):
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex

        result = self.executor.rollback_patch(file_path, commit_hash)

        self.assertTrue(result)
        mock_subprocess.assert_called_once_with(
            ["git", "-C", self.repo_path, "checkout", commit_hash, "--", file_path],
            check=True
        )

    def test_patch_executor_execute_from_lessons(self):
        res = self.executor.execute_from_lessons()
        self.assertIn("status", res)

    def test_patch_verifier_verify_and_apply_syntax_error(self):
        content_with_error = f"print('{uuid.uuid4().hex}') syntax error here"
        patch_data = {"content": content_with_error, "file_path": "test.py"}

        result = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(result)

    @patch("skills.patch_verifier.PatchExecutor.apply_patch")
    def test_patch_verifier_verify_and_apply_success(self, mock_apply_patch):
        mock_apply_patch.return_value = True
        content = f"print('{uuid.uuid4().hex}')"
        patch_data = {"content": content, "file_path": "test.py"}

        result = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(result)
        mock_apply_patch.assert_called_once_with(patch_data)