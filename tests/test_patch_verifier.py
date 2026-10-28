import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
import io
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
        self.rand_repo = f"/tmp/{uuid.uuid4().hex}"
        self.rand_file = f"{uuid.uuid4().hex}.py"
        self.rand_commit = uuid.uuid4().hex
        self.rand_author = f"Author_{uuid.uuid4().hex[:6]}"
        self.rand_msg = f"Message_{uuid.uuid4().hex[:6]}"
        self.inspector = GitInspector(self.rand_repo)
        self.parser = LessonParser(self.inspector)
        self.executor = PatchExecutor(self.rand_repo, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.rand_repo, self.inspector, self.executor)

    @patch("subprocess.run")
    def test_git_inspector_run_git(self, mock_run):
        expected_stdout = f"{uuid.uuid4().hex}\n"
        mock_run.return_value = MagicMock(stdout=expected_stdout)
        args_input = [uuid.uuid4().hex, uuid.uuid4().hex]
        result = self.inspector._run_git(args_input)
        self.assertEqual(result, expected_stdout.strip())
        mock_run.assert_called_once_with(
            ["git", "-C", self.rand_repo] + args_input,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8"
        )

    @patch("skills.patch_verifier.GitInspector._run_git")
    def test_git_inspector_get_commit_history(self, mock_run_git):
        max_count = random.randint(1, 20)
        line_output = f"{self.rand_commit}|{self.rand_author}|{self.rand_msg}"
        mock_run_git.return_value = line_output

        history = self.inspector.get_commit_history(max_count)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["hash"], self.rand_commit)
        self.assertEqual(history[0]["author"], self.rand_author)
        self.assertEqual(history[0]["message"], self.rand_msg)
        mock_run_git.assert_called_once_with(["log", f"-n {max_count}", "--pretty=format:%H|%an|%s"])

    @patch("skills.patch_verifier.GitInspector._run_git")
    def test_git_inspector_get_commit_history_empty(self, mock_run_git):
        mock_run_git.return_value = ""
        history = self.inspector.get_commit_history(random.randint(1, 10))
        self.assertEqual(history, [])

    @patch("skills.patch_verifier.GitInspector._run_git")
    def test_git_inspector_get_file_diff(self, mock_run_git):
        diff_content = f"diff --git a/{self.rand_file} b/{self.rand_file}\n+{uuid.uuid4().hex}"
        mock_run_git.return_value = diff_content
        res = self.inspector.get_file_diff(self.rand_commit)
        self.assertEqual(res, diff_content)
        mock_run_git.assert_called_once_with(["show", self.rand_commit])

    @patch("skills.patch_verifier.GitInspector.get_commit_history")
    def test_git_inspector_analyze_repository(self, mock_get_history):
        commit_dict = {"hash": self.rand_commit, "author": self.rand_author, "message": self.rand_msg}
        mock_get_history.return_value = [commit_dict]
        analysis = self.inspector.analyze_repository()
        self.assertEqual(analysis["total_commits"], 1)
        self.assertEqual(analysis["latest_commit"], commit_dict)

    @patch("skills.patch_verifier.GitInspector._run_git")
    def test_git_inspector_read_file_at_commit(self, mock_run_git):
        file_content = uuid.uuid4().hex
        mock_run_git.return_value = file_content
        res = self.inspector.read_file_at_commit(self.rand_commit, self.rand_file)
        self.assertEqual(res, file_content)
        mock_run_git.assert_called_once_with(["show", f"{self.rand_commit}:{self.rand_file}"])

    @patch("skills.patch_verifier.GitInspector.get_commit_history")
    def test_git_inspector_get_history(self, mock_get_history):
        count = random.randint(1, 5)
        mock_get_history.return_value = [{"hash": uuid.uuid4().hex}]
        res = self.inspector.get_history(count)
        mock_get_history.assert_called_once_with(count)

    @patch("skills.patch_verifier.GitInspector.get_commit_history")
    @patch("skills.patch_verifier.GitInspector.get_file_diff")
    def test_git_inspector_get_latest_changes(self, mock_get_diff, mock_get_history):
        diff_str = uuid.uuid4().hex
        mock_get_history.return_value = [{"hash": self.rand_commit}]
        mock_get_diff.return_value = diff_str
        res = self.inspector.get_latest_changes()
        self.assertEqual(res, diff_str)
        mock_get_diff.assert_called_once_with(self.rand_commit)

    @patch("skills.patch_verifier.GitInspector.get_commit_history")
    def test_git_inspector_get_latest_changes_empty(self, mock_get_history):
        mock_get_history.return_value = []
        res = self.inspector.get_latest_changes()
        self.assertEqual(res, "")

    def test_lesson_parser_parse_lessons(self):
        lessons = self.parser.parse_lessons()
        self.assertTrue(isinstance(lessons, list))
        self.assertGreater(len(lessons), 0)
        self.assertIn("lesson_id", lessons[0])

    def test_lesson_parser_extract_lessons(self):
        extracted = self.parser.extract_lessons(random.randint(1, 15))
        self.assertTrue(isinstance(extracted, dict))
        self.assertIn("lesson_id", extracted)
        self.assertIn("content", extracted)

    def test_hypothesis_generator_generate_hypotheses(self):
        hyps = self.hypothesis_generator = HypothesisGenerator(self.inspector, self.parser)
        res = self.hypothesis_generator.generate_hypotheses(random.randint(1, 10))
        self.assertTrue(isinstance(res, list))
        self.assertIn("id", res[0])
        self.assertIn("weight", res[0])

    def test_hypothesis_generator_prioritize_hypotheses(self):
        gen = HypothesisGenerator(self.inspector, self.parser)
        h1 = {"id": uuid.uuid4().hex, "weight": random.random()}
        h2 = {"id": uuid.uuid4().hex, "weight": random.random() + 1.0}
        prioritized = gen.prioritize_hypotheses([h1, h2])
        self.assertEqual(prioritized[0]["id"], h2["id"])

    @patch("os.makedirs")
    @patch("subprocess.run")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    def test_patch_executor_apply_patch_success(self, mock_file, mock_subprocess, mock_makedirs):
        patch_data = {
            "file_path": self.rand_file,
            "content": uuid.uuid4().hex,
            "commit_message": self.rand_msg
        }
        res = self.executor.apply_patch(patch_data)
        self.assertTrue(res)
        mock_makedirs.assert_called_once()
        mock_file.assert_called_once()
        self.assertEqual(mock_subprocess.call_count, 2)

    def test_patch_executor_apply_patch_invalid_data(self):
        patch_data = {"file_path": ""}
        res = self.executor.apply_patch(patch_data)
        self.assertFalse(res)

    @patch("subprocess.run")
    def test_patch_executor_rollback_patch_success(self, mock_subprocess):
        res = self.executor.rollback_patch(self.rand_file, self.rand_commit)
        self.assertTrue(res)
        mock_subprocess.assert_called_once_with(
            ["git", "-C", self.rand_repo, "checkout", self.rand_commit, "--", self.rand_file],
            check=True
        )

    @patch("subprocess.run")
    def test_patch_executor_rollback_patch_failure(self, mock_subprocess):
        mock_subprocess.side_effect = Exception(uuid.uuid4().hex)
        res = self.executor.rollback_patch(self.rand_file, self.rand_commit)
        self.assertFalse(res)

    def test_patch_executor_execute_from_lessons(self):
        res = self.executor.execute_from_lessons()
        self.assertIn("executed_lessons", res)
        self.assertEqual(res["status"], "success")

    def test_patch_verifier_verify_and_apply_syntax_error(self):
        bad_content = f"print('{uuid.uuid4().hex}') syntax error here"
        patch_data = {"file_path": self.rand_file, "content": bad_content}
        res = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(res)

    @patch("skills.patch_verifier.PatchExecutor.apply_patch")
    def test_patch_verifier_verify_and_apply_success(self, mock_apply):
        mock_apply.return_value = True
        good_content = f"print('{uuid.uuid4().hex}')"
        patch_data = {"file_path": self.rand_file, "content": good_content}
        res = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(res)
        mock_apply.assert_called_once_with(patch_data)