import unittest
from unittest.mock import patch, MagicMock
import os
import subprocess
import uuid
import random
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

    @patch("subprocess.run")
    def test_git_inspector_run_git_success(self, mock_subprocess):
        expected_output = uuid.uuid4().hex
        mock_result = MagicMock()
        mock_result.stdout = f"{expected_output}\n"
        mock_subprocess.return_value = mock_result

        arg_val = uuid.uuid4().hex
        res = self.inspector._run_git([arg_val])

        self.assertEqual(res, expected_output)
        mock_subprocess.assert_called_once_with(
            ["git", "-C", self.repo_path, arg_val],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )

    @patch("skills.patch_verifier.GitInspector._run_git")
    def test_get_commit_history_valid(self, mock_run_git):
        commit_hash = uuid.uuid4().hex
        author_name = uuid.uuid4().hex
        commit_msg = uuid.uuid4().hex
        mock_run_git.return_value = f"{commit_hash}|{author_name}|{commit_msg}"

        count = random.randint(1, 50)
        history = self.inspector.get_commit_history(max_count=count)

        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["hash"], commit_hash)
        self.assertEqual(history[0]["author"], author_name)
        self.assertEqual(history[0]["message"], commit_msg)
        mock_run_git.assert_called_once_with(["log", f"-n {count}", "--pretty=format:%H|%an|%s"])

    @patch("skills.patch_verifier.GitInspector._run_git")
    def test_get_commit_history_empty(self, mock_run_git):
        mock_run_git.return_value = ""
        history = self.inspector.get_commit_history()
        self.assertEqual(history, [])

    @patch("skills.patch_verifier.GitInspector._run_git")
    def test_get_file_diff(self, mock_run_git):
        diff_content = uuid.uuid4().hex
        mock_run_git.return_value = diff_content
        commit_hash = uuid.uuid4().hex

        res = self.inspector.get_file_diff(commit_hash)
        self.assertEqual(res, diff_content)
        mock_run_git.assert_called_once_with(["show", commit_hash])

    @patch("skills.patch_verifier.GitInspector.get_commit_history")
    def test_analyze_repository(self, mock_get_history):
        commit_hash = uuid.uuid4().hex
        mock_get_history.return_value = [{"hash": commit_hash, "author": "test", "message": "test"}]

        analysis = self.inspector.analyze_repository()
        self.assertEqual(analysis["total_commits"], 1)
        self.assertEqual(analysis["latest_commit"]["hash"], commit_hash)

    @patch("skills.patch_verifier.GitInspector._run_git")
    def test_read_file_at_commit(self, mock_run_git):
        file_content = uuid.uuid4().hex
        mock_run_git.return_value = file_content
        commit_hash = uuid.uuid4().hex
        file_path = f"{uuid.uuid4().hex}.py"

        res = self.inspector.read_file_at_commit(commit_hash, file_path)
        self.assertEqual(res, file_content)
        mock_run_git.assert_called_once_with(["show", f"{commit_hash}:{file_path}"])

    @patch("skills.patch_verifier.GitInspector.get_commit_history")
    def test_get_history(self, mock_get_history):
        count = random.randint(1, 20)
        self.inspector.get_history(max_count=count)
        mock_get_history.assert_called_once_with(count)

    @patch("skills.patch_verifier.GitInspector.get_commit_history")
    @patch("skills.patch_verifier.GitInspector.get_file_diff")
    def test_get_latest_changes(self, mock_get_diff, mock_get_history):
        commit_hash = uuid.uuid4().hex
        diff_text = uuid.uuid4().hex
        mock_get_history.return_value = [{"hash": commit_hash}]
        mock_get_diff.return_value = diff_text

        res = self.inspector.get_latest_changes()
        self.assertEqual(res, diff_text)
        mock_get_diff.assert_called_once_with(commit_hash)

    def test_lesson_parser_methods(self):
        lessons = self.parser.parse_lessons()
        self.assertIsInstance(lessons, list)
        extracted = self.parser.extract_lessons()
        self.assertIsInstance(extracted, dict)

    def test_hypothesis_generator_methods(self):
        hyps = self.generator.generate_hypotheses()
        self.assertIsInstance(hyps, list)
        
        input_hyps = [
            {"id": uuid.uuid4().hex, "weight": 0.1},
            {"id": uuid.uuid4().hex, "weight": 0.9},
            {"id": uuid.uuid4().hex, "weight": 0.5}
        ]
        prioritized = self.generator.prioritize_hypotheses(input_hyps)
        self.assertEqual(prioritized[0]["weight"], 0.9)
        self.assertEqual(prioritized[2]["weight"], 0.1)

    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    @patch("os.makedirs")
    @patch("subprocess.run")
    def test_patch_executor_apply_patch_success(self, mock_subprocess, mock_makedirs, mock_file_open):
        file_path = f"{uuid.uuid4().hex}.py"
        content = uuid.uuid4().hex
        commit_msg = uuid.uuid4().hex
        patch_data = {
            "file_path": file_path,
            "content": content,
            "commit_message": commit_msg
        }

        res = self.executor.apply_patch(patch_data)
        self.assertTrue(res)
        mock_makedirs.assert_called_once()
        mock_file_open.assert_called_once()
        self.assertEqual(mock_subprocess.call_count, 2)

    def test_patch_executor_apply_patch_missing_fields(self):
        res = self.executor.apply_patch({"file_path": "", "content": None})
        self.assertFalse(res)

    @patch("builtins.open", side_effect=IOError("Disk full"))
    @patch("os.makedirs")
    def test_patch_executor_apply_patch_exception_handling(self, mock_makedirs, mock_file_open):
        patch_data = {
            "file_path": f"{uuid.uuid4().hex}.py",
            "content": uuid.uuid4().hex
        }
        res = self.executor.apply_patch(patch_data)
        self.assertFalse(res)

    @patch("subprocess.run")
    def test_patch_executor_rollback_patch_success(self, mock_subprocess):
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex
        res = self.executor.rollback_patch(file_path, commit_hash)
        self.assertTrue(res)
        mock_subprocess.assert_called_once_with(
            ["git", "-C", self.repo_path, "checkout", commit_hash, "--", file_path],
            check=True
        )

    @patch("subprocess.run", side_effect=subprocess.SubprocessError("Git error"))
    def test_patch_executor_rollback_patch_failure(self, mock_subprocess):
        res = self.executor.rollback_patch(uuid.uuid4().hex, uuid.uuid4().hex)
        self.assertFalse(res)

    def test_patch_executor_execute_from_lessons(self):
        res = self.executor.execute_from_lessons()
        self.assertIn("status", res)

    @patch("skills.patch_verifier.PatchExecutor.apply_patch")
    def test_patch_verifier_verify_and_apply_syntax_error(self, mock_apply):
        bad_content = f"print({uuid.uuid4().hex}); syntax error here"
        patch_data = {"content": bad_content}
        res = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(res)
        mock_apply.assert_not_called()

    @patch("skills.patch_verifier.PatchExecutor.apply_patch")
    def test_patch_verifier_verify_and_apply_success(self, mock_apply):
        mock_apply.return_value = True
        good_content = f"print('{uuid.uuid4().hex}')"
        patch_data = {"content": good_content, "file_path": f"{uuid.uuid4().hex}.py"}
        res = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(res)
        mock_apply.assert_called_once_with(patch_data)

if __name__ == "__main__":
    unittest.main()