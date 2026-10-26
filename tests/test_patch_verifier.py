import unittest
import os
import random
import uuid
import subprocess
from unittest.mock import patch
from skills.patch_verifier import (
    PatchVerifier,
    GitInspector,
    PatchExecutor,
    HypothesisGeneratorError,
    LessonParserError,
    PatchExecutorError
)

class TestPatchVerifierInquisition(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        subprocess.run(["git", "init", self.repo_path], capture_output=True, text=True, check=True)
        self.inspector = GitInspector(self.repo_path)
        self.executor = PatchExecutor(self.repo_path, self.inspector, None)
        self.verifier = PatchVerifier(self.repo_path, self.inspector, self.executor)

    def tearDown(self):
        subprocess.run(["rm", "-rf", self.repo_path], capture_output=True, text=True)

    def test_verify_and_apply_success(self):
        file_name = f"{uuid.uuid4().hex}.py"
        content_snippet = f"x = {random.randint(1, 100)}\nprint(x)"
        patch_data = {
            "file_path": file_name,
            "content": content_snippet,
            "commit_message": f"commit {uuid.uuid4().hex}"
        }
        res = self.verifier.verify_and_apply(patch_data)
        self.assertTrue(res)

    def test_verify_and_apply_syntax_error(self):
        file_name = f"{uuid.uuid4().hex}.py"
        content_snippet = f"syntax error here {uuid.uuid4().hex}"
        patch_data = {
            "file_path": file_name,
            "content": content_snippet,
            "commit_message": f"commit {uuid.uuid4().hex}"
        }
        res = self.verifier.verify_and_apply(patch_data)
        self.assertFalse(res)

    def test_exceptions_existence(self):
        self.assertTrue(issubclass(HypothesisGeneratorError, Exception))
        self.assertTrue(issubclass(LessonParserError, Exception))
        self.assertTrue(issubclass(PatchExecutorError, Exception))

    def test_verify_and_apply_mocked_executor(self):
        file_name = f"{uuid.uuid4().hex}.txt"
        content_snippet = f"data_{uuid.uuid4().hex}"
        patch_data = {
            "file_path": file_name,
            "content": content_snippet
        }
        with patch.object(self.executor, 'apply_patch', return_value=True) as mock_apply:
            res = self.verifier.verify_and_apply(patch_data)
            self.assertTrue(res)
            mock_apply.assert_called_once_with(patch_data)