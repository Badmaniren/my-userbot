import os
import shutil
import tempfile
import unittest
import uuid
import random

from skills.code_validator import CodeValidator, CodeValidatorError
from skills.patch_executor import PatchExecutor, PatchExecutorError
from skills.git_inspector import GitInspector
from skills.code_patcher import CodePatcher, CodePatcherError


class TestCodePatcherIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.repo_path = self.temp_dir

        self.git_inspector = GitInspector(repo_path=self.repo_path)
        self.validator = CodeValidator(repo_path=self.repo_path)
        self.executor = PatchExecutor(
            repo_path=self.repo_path,
            git_inspector=self.git_inspector
        )

        try:
            self.patcher = CodePatcher(
                repo_path=self.repo_path,
                validator=self.validator,
                executor=self.executor
            )
        except TypeError:
            try:
                self.patcher = CodePatcher(
                    validator=self.validator,
                    executor=self.executor
                )
            except TypeError:
                self.patcher = CodePatcher(self.repo_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _execute_patch(self, patcher, patch_data):
        if hasattr(patcher, "apply_patch"):
            return patcher.apply_patch(patch_data)
        elif hasattr(patcher, "validate_and_apply"):
            return patcher.validate_and_apply(patch_data)
        elif hasattr(patcher, "patch"):
            return patcher.patch(patch_data)
        elif callable(patcher):
            return patcher(patch_data)
        else:
            self.fail("CodePatcher does not expose a supported patch execution method")

    def test_valid_patch_passes_validation_and_is_applied(self):
        random_id = uuid.uuid4().hex
        func_name = f"action_{random_id[:8]}"
        expected_token = f"token_{random_id}"
        file_name = f"module_{random_id[:6]}.py"

        code_content = (
            f"def {func_name}():\n"
            f"    return '{expected_token}'\n"
        )

        patch_data = {
            "file_path": file_name,
            "code": code_content,
            "content": code_content,
            "patch_id": random_id
        }

        result = self._execute_patch(self.patcher, patch_data)
        self.assertTrue(result)

        target_file = os.path.join(self.repo_path, file_name)
        self.assertTrue(os.path.exists(target_file))

        with open(target_file, "r", encoding="utf-8") as f:
            saved_content = f.read()

        self.assertIn(func_name, saved_content)
        self.assertIn(expected_token, saved_content)

    def test_invalid_syntax_patch_fails_validation_and_not_applied(self):
        random_id = uuid.uuid4().hex
        file_name = f"invalid_module_{random_id[:6]}.py"

        invalid_code = (
            f"def broken_function_{random_id[:8]}(:\n"
            f"    return '{random_id}'\n"
        )

        patch_data = {
            "file_path": file_name,
            "code": invalid_code,
            "content": invalid_code,
            "patch_id": random_id
        }

        target_file = os.path.join(self.repo_path, file_name)

        success = False
        try:
            res = self._execute_patch(self.patcher, patch_data)
            success = bool(res)
        except Exception:
            success = False

        self.assertFalse(success)
        self.assertFalse(os.path.exists(target_file))

    def test_forbidden_construct_blocked_by_validator_before_executor(self):
        random_id = uuid.uuid4().hex
        file_name = f"forbidden_{random_id[:6]}.py"

        if hasattr(self.validator, "add_forbidden_construct"):
            self.validator.add_forbidden_construct("eval")

        code_with_forbidden = (
            f"def run_eval_{random_id[:8]}():\n"
            f"    return eval('{random_id}')\n"
        )

        patch_data = {
            "file_path": file_name,
            "code": code_with_forbidden,
            "content": code_with_forbidden,
            "patch_id": random_id
        }

        target_file = os.path.join(self.repo_path, file_name)

        success = False
        try:
            res = self._execute_patch(self.patcher, patch_data)
            success = bool(res)
        except Exception:
            success = False

        self.assertFalse(success)
        self.assertFalse(os.path.exists(target_file))


if __name__ == "__main__":
    unittest.main()