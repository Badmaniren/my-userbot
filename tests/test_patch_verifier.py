import unittest
from unittest.mock import patch, MagicMock
import os
import subprocess
import uuid
import random
import string

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
    def test_git_inspector_run(self, mock_subprocess):
        rand_output = uuid.uuid4().hex
        mock_result = MagicMock()
        mock_result.stdout = rand_output
        mock_subprocess.return_value = mock_result

        arg1 = uuid.uuid4().hex
        res = self.inspector._run_git([arg1])
        self.assertEqual(res, rand_output)
        mock_subprocess.assert_called_once()

    @patch("subprocess.run")
    def test_git_inspector_commit_history(self, mock_subprocess):
        commit_hash = uuid.uuid4().hex
        author = ''.join(random.choices(string.ascii_letters, k=8))
        msg = ''.join(random.choices(string.ascii_letters, k=10))
        mock_output = f"{commit_hash}|{author}|{msg}"

        mock_result = MagicMock()
        mock_result.stdout = mock_output
        mock_subprocess.return_value = mock_result

        count = random.randint(1, 20)
        history = self.inspector.get_commit_history(max_count=count)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["hash"], commit_hash)
        self.assertEqual(history[0]["author"], author)
        self.assertEqual(history[0]["message"], msg)

    @patch("subprocess.run")
    def test_git_inspector_get_file_diff(self, mock_subprocess):
        commit_hash = uuid.uuid4().hex
        diff_content = uuid.uuid4().hex
        mock_result = MagicMock()
        mock_result.stdout = diff_content
        mock_subprocess.return_value = mock_result

        res = self.inspector.get_file_diff(commit_hash)
        self.assertEqual(res, diff_content)

    @patch.object(GitInspector, "get_commit_history")
    def test_git_inspector_analyze_repository(self, mock_commit_history):
        commit_hash = uuid.uuid4().hex
        mock_commit_history.return_value = [{"hash": commit_hash, "author": "tester", "message": "fix"}]

        analysis = self.inspector.analyze_repository()
        self.assertEqual(analysis["total_commits"], 1)
        self.assertEqual(analysis["latest_commit"]["hash"], commit_hash)

    @patch("subprocess.run")
    def test_git_inspector_read_file_at_commit(self, mock_subprocess):
        commit_hash = uuid.uuid4().hex
        file_path = f"{uuid.uuid4().hex}.py"
        file_content = uuid.uuid4().hex

        mock_result = MagicMock()
        mock_result.stdout = file_content
        mock_subprocess.return_value = mock_result

        res = self.inspector.read_file_at_commit(commit_hash, file_path)
        self.assertEqual(res, file_content)

    @patch.object(GitInspector, "get_commit_history")
    def test_git_inspector_get_history(self, mock_commit_history):
        mock_commit_history.return_value = []
        count = random.randint(1, 15)
        res = self.inspector.get_history(max_count=count)
        self.assertEqual(res, [])
        mock_commit_history.assert_called_once_with(count)

    @patch.object(GitInspector, "get_file_diff")
    @patch.object(GitInspector, "get_commit_history")
    def test_git_inspector_get_latest_changes(self, mock_commit_history, mock_get_file_diff):
        commit_hash = uuid.uuid4().hex
        diff_text = uuid.uuid4().hex
        mock_commit_history.return_value = [{"hash": commit_hash}]
        mock_get_file_diff.return_value = diff_text

        res = self.inspector.get_latest_changes()
        self.assertEqual(res, diff_text)

    def test_lesson_parser_parse_lessons(self):
        lessons = self.parser.parse_lessons()
        self.assertIsInstance(lessons, list)
        self.assertGreater(len(lessons), 0)
        self.assertIn("lesson_id", lessons[0])

    def test_lesson_parser_extract_lessons(self):
        count = random.randint(1, 50)
        extracted = self.parser.extract_lessons(max_commits=count)
        self.assertIsInstance(extracted, dict)
        self.assertIn("lesson_id", extracted)

    def test_hypothesis_generator_generate_hypotheses(self):
        count = random.randint(1, 20)
        hypotheses = self.generator.generate_hypotheses(max_commits=count)
        self.assertIsInstance(hypotheses, list)
        self.assertIn("id", hypotheses[0])

    def test_hypothesis_generator_prioritize_hypotheses(self):
        h1_weight = random.uniform(0.1, 0.4)
        h2_weight = random.uniform(0.5, 0.9)
        hypotheses = [
            {"id": uuid.uuid4().hex, "weight": h1_weight},
            {"id": uuid.uuid4().hex, "weight": h2_weight}
        ]
        prioritized = self.generator.prioritize_hypotheses(hypotheses)
        self.assertEqual(prioritized[0]["weight"], h2_weight)
        self.assertEqual(prioritized[1]["weight"], h1_weight)

    @patch("subprocess.run")
    @patch("builtins.open", new_callable=unittest.mock.mock_open)
    @patch("os.makedirs")
    def test_patch_executor_apply_patch_success(self, mock_makedirs, mock_open, mock_subprocess):
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
        mock_open.assert_called_once()
        self.assertEqual(mock_subprocess.call_count, 2)

    def test_patch_executor_apply_patch_missing_data(self):
        patch_data = {"file_path": ""}
        res = self.executor.apply_patch(patch_data)
        self.assertFalse(res)

    @patch("subprocess.run")
    def test_patch_executor_rollback_patch_success(self, mock_subprocess):
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex
        res = self.executor.rollback_patch(file_path, commit_hash)
        self.assertTrue(res)
        mock_subprocess.assert_called_once()

    @patch("subprocess.run", side_effect=Exception("Git rollback failed"))
    def test_patch_executor_rollback_patch_failure(self, mock_subprocess):
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex
        res = self.executor.rollback_patch(file_path, commit_hash)
        self.assertFalse(res)

    def test_patch_executor_execute_from_lessons(self):
        res = self.executor.execute_from_lessons()
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("status"), "success")

    def test_patch_verifier_verify_and_apply_syntax_error(self):
        bad_content = uuid.uuid4().hex + " syntax error here " + uuid.uuid4().hex
        patch_data = {"content": bad_content}
        res = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(res)

    @patch.object(PatchExecutor, "apply_patch")
    def test_patch_verifier_verify_and_apply_success(self, mock_apply):
        mock_apply.return_value = True
        good_content = uuid.uuid4().hex
        patch_data = {"content": good_content}
        res = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(res)
        mock_apply.assert_called_once_with(patch_data)