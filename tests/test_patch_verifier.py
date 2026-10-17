import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
import string
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
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.inspector = GitInspector(self.repo_path)
        self.parser = LessonParser(self.inspector)
        self.generator = HypothesisGenerator(self.inspector, self.parser)
        self.executor = PatchExecutor(self.repo_path, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.repo_path, self.inspector, self.executor)

    def test_git_inspector_run_git_success(self):
        random_hash = uuid.uuid4().hex
        random_author = "".join(random.choices(string.ascii_letters, k=8))
        random_message = "".join(random.choices(string.ascii_letters, k=15))
        mock_output = f"{random_hash}|{random_author}|{random_message}\n"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=mock_output, stderr="")
            history = self.inspector.get_commit_history(max_count=1)
            
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["hash"], random_hash)
            self.assertEqual(history[0]["author"], random_author)
            self.assertEqual(history[0]["message"], random_message)

    def test_git_inspector_empty_history(self):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout="", stderr="")
            history = self.inspector.get_commit_history(max_count=5)
            self.assertEqual(history, [])

    def test_git_inspector_get_file_diff(self):
        commit_hash = uuid.uuid4().hex
        expected_diff = f"diff --git a/{uuid.uuid4().hex}.py b/{uuid.uuid4().hex}.py"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=expected_diff, stderr="")
            diff = self.inspector.get_file_diff(commit_hash)
            self.assertEqual(diff, expected_diff)

    def test_git_inspector_analyze_repository(self):
        random_hash = uuid.uuid4().hex
        random_author = "".join(random.choices(string.ascii_letters, k=6))
        random_msg = "".join(random.choices(string.ascii_letters, k=10))
        mock_output = f"{random_hash}|{random_author}|{random_msg}\n"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=mock_output, stderr="")
            analysis = self.inspector.analyze_repository()
            
            self.assertEqual(analysis["total_commits"], 1)
            self.assertIsNotNone(analysis["latest_commit"])
            self.assertEqual(analysis["latest_commit"]["hash"], random_hash)

    def test_git_inspector_read_file_at_commit(self):
        commit_hash = uuid.uuid4().hex
        file_path = f"{uuid.uuid4().hex}.py"
        file_content = f"print('{uuid.uuid4().hex}')"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=file_content, stderr="")
            content = self.inspector.read_file_at_commit(commit_hash, file_path)
            self.assertEqual(content, file_content)

    def test_git_inspector_get_history_and_latest(self):
        random_hash = uuid.uuid4().hex
        mock_output = f"{random_hash}|Tester|Initial commit\n"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=mock_output, stderr="")
            history = self.inspector.get_history(max_count=2)
            self.assertEqual(len(history), 1)

            latest_changes = self.inspector.get_latest_changes()
            self.assertIsInstance(latest_changes, str)

    def test_lesson_parser_extraction(self):
        lessons = self.parser.parse_lessons()
        self.assertIsInstance(lessons, list)
        self.assertTrue(len(lessons) > 0)

        extracted = self.parser.extract_lessons(max_commits=3)
        self.assertIn("lesson_id", extracted)
        self.assertIn("content", extracted)

    def test_hypothesis_generator_prioritization(self):
        hyp_1_weight = random.uniform(0.1, 0.4)
        hyp_2_weight = random.uniform(0.5, 0.9)
        
        hypotheses = [
            {"id": uuid.uuid4().hex, "weight": hyp_1_weight, "target": "a.py"},
            {"id": uuid.uuid4().hex, "weight": hyp_2_weight, "target": "b.py"}
        ]

        prioritized = self.generator.prioritize_hypotheses(hypotheses)
        self.assertEqual(prioritized[0]["weight"], hyp_2_weight)
        self.assertEqual(prioritized[1]["weight"], hyp_1_weight)

        generated = self.generator.generate_hypotheses(max_commits=2)
        self.assertIsInstance(generated, list)

    def test_patch_executor_apply_success(self):
        file_path = f"{uuid.uuid4().hex}.py"
        content = f"# {uuid.uuid4().hex}"
        commit_msg = f"feat: {uuid.uuid4().hex}"

        patch_data = {
            "file_path": file_path,
            "content": content,
            "commit_message": commit_msg
        }

        with patch("builtins.open", new_callable=unittest.mock.mock_open()) as mock_file, \
             patch("os.makedirs") as mock_makedirs, \
             patch("subprocess.run") as mock_subprocess:
            
            result = self.executor.apply_patch(patch_data)
            self.assertTrue(result)
            mock_makedirs.assert_called_once()
            mock_file.assert_called_once()
            self.assertEqual(mock_subprocess.call_count, 2)

    def test_patch_executor_apply_missing_fields(self):
        patch_data = {"file_path": "", "content": None}
        result = self.executor.apply_patch(patch_data)
        self.assertFalse(result)

    def test_patch_executor_apply_exception(self):
        patch_data = {
            "file_path": f"{uuid.uuid4().hex}.py",
            "content": uuid.uuid4().hex
        }

        with patch("builtins.open", side_effect=Exception("Disk failure")):
            result = self.executor.apply_patch(patch_data)
            self.assertFalse(result)

    def test_patch_executor_rollback_success(self):
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            result = self.executor.rollback_patch(file_path, commit_hash)
            self.assertTrue(result)

    def test_patch_executor_rollback_exception(self):
        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex

        with patch("subprocess.run", side_effect=Exception("Git checkout failed")):
            result = self.executor.rollback_patch(file_path, commit_hash)
            self.assertFalse(result)

    def test_patch_executor_execute_from_lessons(self):
        res = self.executor.execute_from_lessons()
        self.assertIn("executed_lessons", res)
        self.assertIn("status", res)

    def test_patch_verifier_syntax_error(self):
        patch_data = {
            "file_path": f"{uuid.uuid4().hex}.py",
            "content": "def broken(): syntax error here"
        }
        result = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(result)

    def test_patch_verifier_valid_patch(self):
        file_path = f"{uuid.uuid4().hex}.py"
        patch_data = {
            "file_path": file_path,
            "content": f"def safe_func_{uuid.uuid4().hex}(): return True"
        }

        with patch.object(self.executor, "apply_patch", return_value=True) as mock_apply:
            result = self.verifier.verify_and_apply(patch_data)
            self.assertTrue(result)
            mock_apply.assert_called_once_with(patch_data)