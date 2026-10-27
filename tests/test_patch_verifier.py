import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import os
import io
import subprocess
import ast

from skills.patch_verifier import (
    GitInspector,
    LessonParser,
    HypothesisGenerator,
    PatchExecutor,
    PatchVerifier,
    PatchVerifierError,
    HypothesisGeneratorError,
    LessonParserError,
    PatchExecutorError
)


class TestPatchVerifierInquisition(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
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
        mock_result = MagicMock()
        mock_result.stdout = f"{random_hash}|{random_author}|{random_message}\n"

        with patch("subprocess.run", return_value=mock_result) as mock_run:
            history = inspector.get_commit_history(max_count=random.randint(1, 50))
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["hash"], random_hash)
            self.assertEqual(history[0]["author"], random_author)
            self.assertEqual(history[0]["message"], random_message)
            mock_run.assert_called_once()

    def test_git_inspector_empty_output(self):
        inspector = GitInspector(self.repo_path)
        mock_result = MagicMock()
        mock_result.stdout = ""

        with patch("subprocess.run", return_value=mock_result):
            history = inspector.get_commit_history()
            self.assertEqual(history, [])
            diff = inspector.get_latest_changes()
            self.assertEqual(diff, "")

    def test_lesson_parser_extraction(self):
        parser = LessonParser(self.inspector_mock)
        lessons = parser.parse_lessons()
        self.assertIsInstance(lessons, list)
        extracted = parser.extract_lessons(max_commits=random.randint(1, 10))
        self.assertIsInstance(extracted, dict)
        self.assertIn("lesson_id", extracted)

    def test_hypothesis_generator_prioritize(self):
        parser_mock = MagicMock(spec=LessonParser)
        generator = HypothesisGenerator(self.inspector_mock, parser_mock)
        
        id_1 = uuid.uuid4().hex
        id_2 = uuid.uuid4().hex
        weight_1 = random.random()
        weight_2 = weight_1 + random.uniform(0.1, 1.0)

        hypotheses = [
            {"id": id_1, "weight": weight_1, "target": uuid.uuid4().hex},
            {"id": id_2, "weight": weight_2, "target": uuid.uuid4().hex}
        ]

        prioritized = generator.prioritize_hypotheses(hypotheses)
        self.assertEqual(prioritized[0]["id"], id_2)
        self.assertEqual(prioritized[1]["id"], id_1)

        generated = generator.generate_hypotheses()
        self.assertIsInstance(generated, list)

    def test_patch_executor_apply_success(self):
        parser_mock = MagicMock(spec=LessonParser)
        executor = PatchExecutor(self.repo_path, self.inspector_mock, parser_mock)

        file_path = f"{uuid.uuid4().hex}.py"
        content = f"x = {random.randint(1, 100)}"
        commit_message = uuid.uuid4().hex
        patch_data = {
            "file_path": file_path,
            "content": content,
            "commit_message": commit_message
        }

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file, \
             patch("os.makedirs") as mock_dirs, \
             patch("subprocess.run") as mock_subproc:
            
            result = executor.apply_patch(patch_data)
            self.assertTrue(result)
            mock_file.assert_called_once()
            mock_dirs.assert_called_once()
            self.assertEqual(mock_subproc.call_count, 2)

    def test_patch_executor_apply_failure_missing_data(self):
        parser_mock = MagicMock(spec=LessonParser)
        executor = PatchExecutor(self.repo_path, self.inspector_mock, parser_mock)

        self.assertFalse(executor.apply_patch({}))
        self.assertFalse(executor.apply_patch({"file_path": uuid.uuid4().hex}))
        self.assertFalse(executor.apply_patch({"content": uuid.uuid4().hex}))

    def test_patch_executor_rollback_success(self):
        parser_mock = MagicMock(spec=LessonParser)
        executor = PatchExecutor(self.repo_path, self.inspector_mock, parser_mock)

        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex

        with patch("subprocess.run") as mock_subproc:
            result = executor.rollback_patch(file_path, commit_hash)
            self.assertTrue(result)
            mock_subproc.assert_called_once()

    def test_patch_executor_rollback_failure(self):
        parser_mock = MagicMock(spec=LessonParser)
        executor = PatchExecutor(self.repo_path, self.inspector_mock, parser_mock)

        file_path = f"{uuid.uuid4().hex}.py"
        commit_hash = uuid.uuid4().hex

        with patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "git")):
            result = executor.rollback_patch(file_path, commit_hash)
            self.assertFalse(result)

    def test_patch_executor_execute_from_lessons(self):
        parser_mock = MagicMock(spec=LessonParser)
        executor = PatchExecutor(self.repo_path, self.inspector_mock, parser_mock)
        res = executor.execute_from_lessons()
        self.assertIn("status", res)

    def test_patch_verifier_empty_content(self):
        patch_data = {"content": ""}
        result = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(result)
        self.executor_mock.apply_patch.assert_not_called()

    def test_patch_verifier_syntax_error(self):
        random_var = uuid.uuid4().hex
        malformed_code = f"def {random_var}(:"
        patch_data = {"content": malformed_code, "file_path": f"{uuid.uuid4().hex}.py"}

        result = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(result)
        self.executor_mock.apply_patch.assert_not_called()

    def test_patch_verifier_success(self):
        random_val = random.randint(100, 999)
        valid_code = f"x = {random_val}\nprint(x)"
        patch_data = {"content": valid_code, "file_path": f"{uuid.uuid4().hex}.py"}

        self.executor_mock.apply_patch.return_value = True

        result = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(result)
        self.executor_mock.apply_patch.assert_called_once_with(patch_data)

    def test_patch_verifier_positional_args(self):
        file_path = f"{uuid.uuid4().hex}.py"
        valid_code = "a = 10\n"
        self.executor_mock.apply_patch.return_value = True

        result = self.verifier.verify_and_apply(file_path, valid_code)
        self.assertTrue(result)
        self.executor_mock.apply_patch.assert_called_once()

    def test_patch_verifier_verify_method(self):
        self.assertTrue(self.verifier.verify("def test(): pass"))
        self.assertFalse(self.verifier.verify("def test(:"))
        self.assertFalse(self.verifier.verify(""))

    def test_patch_verifier_default_init(self):
        verifier = PatchVerifier(self.repo_path)
        self.assertIsNotNone(verifier.inspector)
        self.assertIsNotNone(verifier.executor)

    def test_exceptions_instantiation(self):
        err_msg = uuid.uuid4().hex
        exc0 = PatchVerifierError(err_msg)
        exc1 = HypothesisGeneratorError(err_msg)
        exc2 = LessonParserError(err_msg)
        exc3 = PatchExecutorError(err_msg)
        self.assertIsInstance(exc0, Exception)
        self.assertIsInstance(exc1, Exception)
        self.assertIsInstance(exc2, Exception)
        self.assertIsInstance(exc3, Exception)


if __name__ == "__main__":
    unittest.main()