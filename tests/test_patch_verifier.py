import unittest
from unittest.mock import patch, MagicMock
import os
import subprocess
import uuid
import random
import io
import ast

from skills.patch_verifier import (
    PatchVerifier,
    GitInspector,
    PatchExecutor,
    HypothesisGeneratorError,
    LessonParserError,
    PatchExecutorError
)
from skills.code_validator import CodeValidatorASTError

class TestPatchVerifierAndCodeValidatorInquisition(unittest.TestCase):

    def setUp(self):
        self.repo_path = os.path.join("/tmp", f"repo_{uuid.uuid4().hex}")
        self.file_path = f"{uuid.uuid4().hex}.py"
        self.inspector = MagicMock(spec=GitInspector)
        self.executor = MagicMock(spec=PatchExecutor)
        self.verifier = PatchVerifier(self.repo_path, self.inspector, self.executor)

    def test_patch_verifier_success(self):
        rnd_content = f"print('{uuid.uuid4().hex}')"
        patch_data = {
            "file_path": self.file_path,
            "content": rnd_content,
            "commit_message": f"msg_{uuid.uuid4().hex}"
        }
        self.executor.apply_patch.return_value = True

        result = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(result)
        self.executor.apply_patch.assert_called_once_with(patch_data)

    def test_patch_verifier_syntax_error(self):
        rnd_content = f"syntax error here {uuid.uuid4().hex}"
        patch_data = {
            "file_path": self.file_path,
            "content": rnd_content,
            "commit_message": f"msg_{uuid.uuid4().hex}"
        }

        result = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(result)
        self.executor.apply_patch.assert_not_called()

    def test_git_inspector_run_git_subprocess_mock(self):
        inspector = GitInspector(self.repo_path)
        random_hash = uuid.uuid4().hex
        random_author = uuid.uuid4().hex
        random_msg = uuid.uuid4().hex
        git_output = f"{random_hash}|{random_author}|{random_msg}"

        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(stdout=git_output)
            history = inspector.get_commit_history(max_count=random.randint(1, 10))
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]["hash"], random_hash)
            self.assertEqual(history[0]["author"], random_author)
            self.assertEqual(history[0]["message"], random_msg)

    def test_patch_executor_apply_patch_io(self):
        from skills.patch_verifier import LessonParser
        parser = MagicMock(spec=LessonParser)
        executor = PatchExecutor(self.repo_path, self.inspector, parser)
        
        rnd_file = f"sub/{uuid.uuid4().hex}.py"
        rnd_content = f"x = {random.randint(100, 999)}"
        patch_data = {
            "file_path": rnd_file,
            "content": rnd_content,
            "commit_message": f"commit_{uuid.uuid4().hex}"
        }

        with patch("builtins.open", new_callable=unittest.mock.mock_open()) as mock_file, \
             patch("os.makedirs") as mock_makedirs, \
             patch("subprocess.run") as mock_subproc:
            
            res = executor.apply_patch(patch_data)
            self.assertTrue(res)
            mock_makedirs.assert_called_once()
            mock_file.assert_called_once()
            mock_file.return_value.__enter__.return_value.write.assert_called_once_with(rnd_content)
            self.assertEqual(mock_subproc.call_count, 2)

    def test_code_validator_ast_error_handling(self):
        from skills.code_validator import CodeValidator
        validator = CodeValidator()
        malformed_code = f"def invalid_syntax_{uuid.uuid4().hex[:6]}(:"

        with self.assertRaises(CodeValidatorASTError):
            validator.validate_code(malformed_code)

    def test_patch_verifier_pipeline_integration(self):
        test_dir = os.path.join("/tmp", f"test_dir_{uuid.uuid4().hex}")
        os.makedirs(test_dir, exist_ok=True)

        try:
            with patch("subprocess.run") as mock_subproc:
                mock_subproc.return_value = MagicMock(returncode=0, stdout="", stderr="")
                inspector = GitInspector(test_dir)
                parser = MagicMock()
                executor = PatchExecutor(test_dir, inspector, parser)
                verifier = PatchVerifier(test_dir, inspector, executor)

                rnd_file = f"{uuid.uuid4().hex}.py"
                patch_data = {
                    "file_path": rnd_file,
                    "content": f"val = {random.randint(1, 500)}",
                    "commit_message": f"msg_{uuid.uuid4().hex}"
                }

                with patch("builtins.open", unittest.mock.mock_open()), \
                     patch("os.makedirs"):
                    res = verifier.verify_and_apply(patch_data)
                    self.assertTrue(res)
        finally:
            if os.path.exists(test_dir):
                import shutil
                shutil.rmtree(test_dir, ignore_errors=True)

    def test_patch_verifier_syntax_error_rejection_pipeline(self):
        test_dir = os.path.join("/tmp", f"test_dir_{uuid.uuid4().hex}")
        os.makedirs(test_dir, exist_ok=True)

        try:
            with patch("subprocess.run") as mock_subproc:
                mock_subproc.return_value = MagicMock(returncode=0, stdout="", stderr="")
                inspector = GitInspector(test_dir)
                parser = MagicMock()
                executor = PatchExecutor(test_dir, inspector, parser)
                verifier = PatchVerifier(test_dir, inspector, executor)

                rnd_file = f"{uuid.uuid4().hex}.py"
                patch_data = {
                    "file_path": rnd_file,
                    "content": f"syntax error here {uuid.uuid4().hex}",
                    "commit_message": f"msg_{uuid.uuid4().hex}"
                }

                res = verifier.verify_and_apply(patch_data)
                self.assertFalse(res)
        finally:
            if os.path.exists(test_dir):
                import shutil
                shutil.rmtree(test_dir, ignore_errors=True)