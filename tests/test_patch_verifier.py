import unittest
from unittest.mock import patch, MagicMock
import os
import subprocess
import uuid
import random
import io
import ast

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

class TestPatchVerifierInquisition(unittest.TestCase):

    def setUp(self):
        self.rand_suffix = uuid.uuid4().hex[:8]
        self.repo_path = os.path.join("/tmp", f"repo_{self.rand_suffix}")
        self.file_path = f"src_{self.rand_suffix}.py"
        self.commit_hash = uuid.uuid4().hex
        self.author_name = f"Author_{self.rand_suffix}"
        self.commit_msg = f"Commit_{self.rand_suffix}"

        self.inspector = GitInspector(self.repo_path)
        self.parser = LessonParser(self.inspector)
        self.hypothesis_generator = HypothesisGenerator(self.inspector, self.parser)
        self.executor = PatchExecutor(self.repo_path, self.inspector, self.parser)
        self.verifier = PatchVerifier(self.repo_path, self.inspector, self.executor)

    def test_git_inspector_run_git_success(self):
        with patch("subprocess.run") as mock_run:
            mock_res = MagicMock()
            mock_res.stdout = f"{self.commit_hash}|{self.author_name}|{self.commit_msg}\n"
            mock_run.return_value = mock_res
            
            history = self.inspector.get_commit_history(max_count=1)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["hash"], self.commit_hash)
            self.assertEqual(history[0]["author"], self.author_name)
            self.assertEqual(history[0]["message"], self.commit_msg)

    def test_git_inspector_empty_history(self):
        with patch("subprocess.run") as mock_run:
            mock_res = MagicMock()
            mock_res.stdout = ""
            mock_run.return_value = mock_res

            history = self.inspector.get_commit_history()
            self.assertEqual(history, [])

    def test_git_inspector_get_file_diff(self):
        with patch("subprocess.run") as mock_run:
            diff_content = f"diff --git a/{self.file_path} b/{self.file_path}\n+random_change_{self.rand_suffix}"
            mock_res = MagicMock()
            mock_res.stdout = diff_content
            mock_run.return_value = mock_res

            res = self.inspector.get_file_diff(self.commit_hash)
            self.assertIn(self.file_path, res)
            self.assertIn(self.rand_suffix, res)

    def test_git_inspector_analyze_repository(self):
        with patch.object(self.inspector, "get_commit_history") as mock_history:
            mock_history.return_value = [{"hash": self.commit_hash, "author": self.author_name, "message": self.commit_msg}]
            analysis = self.inspector.analyze_repository()
            self.assertEqual(analysis["total_commits"], 1)
            self.assertEqual(analysis["latest_commit"]["hash"], self.commit_hash)

    def test_git_inspector_read_file_at_commit(self):
        with patch("subprocess.run") as mock_run:
            file_content = f"print('{self.rand_suffix}')"
            mock_res = MagicMock()
            mock_res.stdout = file_content
            mock_run.return_value = mock_res

            content = self.inspector.read_file_at_commit(self.commit_hash, self.file_path)
            self.assertEqual(content, file_content)

    def test_git_inspector_get_history_and_latest(self):
        with patch.object(self.inspector, "get_commit_history") as mock_history, \
             patch.object(self.inspector, "get_file_diff") as mock_diff:
            mock_history.return_value = [{"hash": self.commit_hash, "author": self.author_name, "message": self.commit_msg}]
            mock_diff.return_value = f"content_{self.rand_suffix}"

            hist = self.inspector.get_history(max_count=5)
            self.assertEqual(len(hist), 1)

            latest = self.inspector.get_latest_changes()
            self.assertIn(self.rand_suffix, latest)

    def test_lesson_parser_methods(self):
        lessons = self.parser.parse_lessons()
        self.assertIsInstance(lessons, list)
        self.assertGreater(len(lessons), 0)

        extracted = self.parser.extract_lessons(max_commits=random.randint(1, 15))
        self.assertIsInstance(extracted, dict)
        self.assertIn("lesson_id", extracted)

    def test_hypothesis_generator_and_prioritizer(self):
        hypotheses = self.hypothesis_generator.generate_hypotheses(max_commits=5)
        self.assertIsInstance(hypotheses, list)
        self.assertGreater(len(hypotheses), 0)
        
        weighted_hypotheses = [
            {"id": f"hyp_low_{self.rand_suffix}", "weight": 0.1, "target": self.file_path},
            {"id": f"hyp_high_{self.rand_suffix}", "weight": 0.9, "target": self.file_path}
        ]
        prioritized = self.hypothesis_generator.prioritize_hypotheses(weighted_hypotheses)
        self.assertEqual(prioritized[0]["weight"], 0.9)

    def test_patch_executor_apply_success(self):
        patch_data = {
            "file_path": self.file_path,
            "content": f"data_{self.rand_suffix}",
            "commit_message": self.commit_msg
        }
        with patch("os.makedirs") as mock_mkdirs, \
             patch("builtins.open", new_callable=unittest.mock.mock_open()) as mock_file, \
             patch("subprocess.run") as mock_run:
            
            res = self.executor.apply_patch(patch_data)
            self.assertTrue(res)
            mock_file.assert_called_once()
            self.assertEqual(mock_run.call_count, 2)

    def test_patch_executor_apply_failure_missing_data(self):
        patch_data = {"file_path": self.file_path}
        res = self.executor.apply_patch(patch_data)
        self.assertFalse(res)

    def test_patch_executor_rollback_and_execute_lessons(self):
        with patch("subprocess.run") as mock_run:
            res_rollback = self.executor.rollback_patch(self.file_path, self.commit_hash)
            self.assertTrue(res_rollback)
            mock_run.assert_called_once()

            res_lessons = self.executor.execute_from_lessons()
            self.assertIsInstance(res_lessons, dict)
            self.assertEqual(res_lessons["status"], "success")

    def test_patch_verifier_verify_and_apply_success(self):
        patch_data = {
            "file_path": self.file_path,
            "content": f"valid_code_{self.rand_suffix}",
            "commit_message": self.commit_msg
        }
        with patch.object(self.executor, "apply_patch", return_value=True) as mock_apply:
            res = self.verifier.verify_and_apply(patch_data)
            self.assertTrue(res)
            mock_apply.assert_called_once_with(patch_data)

    def test_patch_verifier_verify_and_apply_syntax_error(self):
        patch_data = {
            "file_path": self.file_path,
            "content": f"syntax error here {self.rand_suffix}",
            "commit_message": self.commit_msg
        }
        with patch.object(self.executor, "apply_patch") as mock_apply:
            res = self.verifier.verify_and_apply(patch_data)
            self.assertFalse(res)
            mock_apply.assert_not_called()