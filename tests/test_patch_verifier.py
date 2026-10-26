import unittest
from unittest.mock import patch, MagicMock
import os
import uuid
import random
import io
import subprocess

from skills.patch_verifier import (
    PatchVerifier,
    GitInspector,
    LessonParser,
    HypothesisGenerator,
    PatchExecutor,
    HypothesisGeneratorError,
    LessonParserError,
    PatchExecutorError
)
from skills.patch_sanitizer import PatchSanitizerError

class TestPatchVerifierModuleInquisition(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.inspector_mock = MagicMock(spec=GitInspector)
        self.executor_mock = MagicMock(spec=PatchExecutor)
        self.verifier = PatchVerifier(
            repo_path=self.repo_path,
            inspector=self.inspector_mock,
            executor=self.executor_mock
        )

    def test_git_inspector_run_git_success(self):
        inspector = GitInspector(self.repo_path)
        random_hash = uuid.uuid4().hex
        random_author = uuid.uuid4().hex
        random_message = uuid.uuid4().hex
        git_output = f"{random_hash}|{random_author}|{random_message}"

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = git_output
            mock_run.return_value = mock_result

            history = inspector.get_commit_history(max_count=1)
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["hash"], random_hash)
            self.assertEqual(history[0]["author"], random_author)
            self.assertEqual(history[0]["message"], random_message)

    def test_git_inspector_get_file_diff(self):
        inspector = GitInspector(self.repo_path)
        random_diff = uuid.uuid4().hex

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = random_diff
            mock_run.return_value = mock_result

            res = inspector.get_file_diff("abc1234")
            self.assertEqual(res, random_diff)

    def test_git_inspector_analyze_repository(self):
        inspector = GitInspector(self.repo_path)
        random_hash = uuid.uuid4().hex
        git_output = f"{random_hash}|author|msg"

        with patch("subprocess.run") as mock_run:
            mock_result = MagicMock()
            mock_result.stdout = git_output
            mock_run.return_value = mock_result

            analysis = inspector.analyze_repository()
            self.assertEqual(analysis["total_commits"], 1)
            self.assertEqual(analysis["latest_commit"]["hash"], random_hash)

    def test_lesson_parser_methods(self):
        parser = LessonParser(self.inspector_mock)
        lessons = parser.parse_lessons()
        self.assertIsInstance(lessons, list)
        extracted = parser.extract_lessons(max_commits=random.randint(1, 5))
        self.assertIsInstance(extracted, (list, dict))

    def test_hypothesis_generator_methods(self):
        generator = HypothesisGenerator(self.inspector_mock, LessonParser(self.inspector_mock))
        hyps = generator.generate_hypotheses()
        self.assertIsInstance(hyps, list)
        
        random_weights = [{"weight": random.random()} for _ in range(3)]
        prioritized = generator.prioritize_hypotheses(random_weights)
        self.assertEqual(len(prioritized), 3)

    def test_patch_executor_apply_patch_success(self):
        executor = PatchExecutor(self.repo_path, self.inspector_mock, LessonParser(self.inspector_mock))
        random_file = f"{uuid.uuid4().hex}.py"
        random_content = uuid.uuid4().hex
        random_msg = uuid.uuid4().hex
        patch_data = {
            "file_path": random_file,
            "content": random_content,
            "commit_message": random_msg
        }

        with patch("os.makedirs") as mock_dirs, \
             patch("builtins.open", unittest.mock.mock_open()) as mock_file, \
             patch("subprocess.run") as mock_run:
            
            result = executor.apply_patch(patch_data)
            self.assertTrue(result)
            mock_dirs.assert_called_once()
            mock_file.assert_called_once()

    def test_patch_executor_rollback_patch(self):
        executor = PatchExecutor(self.repo_path, self.inspector_mock, LessonParser(self.inspector_mock))
        random_file = f"{uuid.uuid4().hex}.py"
        random_hash = uuid.uuid4().hex

        with patch("subprocess.run") as mock_run:
            res = executor.rollback_patch(random_file, random_hash)
            self.assertTrue(res)

    def test_patch_executor_execute_from_lessons(self):
        executor = PatchExecutor(self.repo_path, self.inspector_mock, LessonParser(self.inspector_mock))
        res = executor.execute_from_lessons()
        self.assertIn("status", res)

    def test_patch_verifier_verify_and_apply_empty_content(self):
        patch_data = {"content": ""}
        result = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(result)

    def test_patch_verifier_verify_and_apply_syntax_error(self):
        random_error_word = uuid.uuid4().hex
        patch_data = {"content": f"syntax error here {random_error_word}"}
        result = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(result)

    def test_patch_verifier_verify_and_apply_sanitizer_exception(self):
        random_content = uuid.uuid4().hex
        patch_data = {"content": random_content}

        with patch.object(self.verifier.sanitizer, "sanitize", side_effect=PatchSanitizerError(uuid.uuid4().hex)):
            result = self.verifier.verify_and_apply(patch_data)
            self.assertFalse(result)

    def test_patch_verifier_verify_and_apply_success(self):
        random_content = uuid.uuid4().hex
        random_sanitized = uuid.uuid4().hex
        patch_data = {"content": random_content, "file_path": f"{uuid.uuid4().hex}.py"}

        with patch.object(self.verifier.sanitizer, "sanitize", return_value=random_sanitized):
            self.executor_mock.apply_patch.return_value = True
            result = self.verifier.verify_and_apply(patch_data)
            self.assertTrue(result)
            self.executor_mock.apply_patch.assert_called_once()
            called_arg = self.executor_mock.apply_patch.call_args[0][0]
            self.assertEqual(called_arg["content"], random_sanitized)
