import unittest
from unittest.mock import patch, MagicMock
import subprocess
import uuid
import random
import string
import io
from skills.patch_runner import PatchRunner, PatchRunnerError, run_patch

class TestPatchRunner(unittest.TestCase):

    def setUp(self):
        self.random_repo_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}"
        self.random_patch_path = f"/{uuid.uuid4().hex}/{uuid.uuid4().hex}.patch"

        random_str = "".join(random.choices(string.ascii_letters + string.whitespace, k=50))
        self.patch_content = f"diff --git a/{uuid.uuid4().hex} b/{uuid.uuid4().hex}\n{random_str}"

        self.runner = PatchRunner(repo_path=self.random_repo_path)

    @patch("skills.patch_runner.PatchApplier")
    @patch("skills.patch_runner.PatchChecker")
    @patch("skills.patch_runner.PatchSanitizer")
    def test_run_patch_success(self, mock_sanitizer_cls, mock_checker_cls, mock_applier_cls):
        expected_sanitized = f"sanitized_{uuid.uuid4().hex}"
        expected_check_result = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_status = {uuid.uuid4().hex: True}

        mock_sanitizer = mock_sanitizer_cls.return_value
        mock_sanitizer.sanitize.return_value = expected_sanitized

        mock_checker = mock_checker_cls.return_value
        mock_checker.check.return_value = expected_check_result

        mock_applier = mock_applier_cls.return_value
        mock_applier.apply.return_value = expected_status

        result = self.runner.run_patch(self.patch_content)

        mock_sanitizer.sanitize.assert_called_once_with(self.patch_content)
        mock_checker.check.assert_called_once_with(expected_sanitized)
        mock_applier.apply.assert_called_once_with(expected_sanitized, self.random_repo_path)
        self.assertEqual(result, expected_status)

    @patch("skills.patch_runner.PatchSanitizer")
    def test_run_patch_sanitizer_exception(self, mock_sanitizer_cls):
        err_msg = uuid.uuid4().hex
        mock_sanitizer = mock_sanitizer_cls.return_value
        mock_sanitizer.sanitize.side_effect = Exception(err_msg)

        with self.assertRaises(PatchRunnerError) as ctx:
            self.runner.run_patch(self.patch_content)
        self.assertIn(err_msg, str(ctx.exception))

    @patch("skills.patch_runner.PatchChecker")
    @patch("skills.patch_runner.PatchSanitizer")
    def test_run_patch_checker_exception(self, mock_sanitizer_cls, mock_checker_cls):
        err_msg = uuid.uuid4().hex
        mock_sanitizer = mock_sanitizer_cls.return_value
        mock_sanitizer.sanitize.return_value = uuid.uuid4().hex

        mock_checker = mock_checker_cls.return_value
        mock_checker.check.side_effect = Exception(err_msg)

        with self.assertRaises(PatchRunnerError) as ctx:
            self.runner.run_patch(self.patch_content)
        self.assertIn(err_msg, str(ctx.exception))

    @patch("skills.patch_runner.PatchApplier")
    @patch("skills.patch_runner.PatchChecker")
    @patch("skills.patch_runner.PatchSanitizer")
    def test_run_patch_applier_exception(self, mock_sanitizer_cls, mock_checker_cls, mock_applier_cls):
        err_msg = uuid.uuid4().hex
        mock_sanitizer = mock_sanitizer_cls.return_value
        mock_sanitizer.sanitize.return_value = uuid.uuid4().hex

        mock_checker = mock_checker_cls.return_value
        mock_checker.check.return_value = True

        mock_applier = mock_applier_cls.return_value
        mock_applier.apply.side_effect = Exception(err_msg)

        with self.assertRaises(PatchRunnerError) as ctx:
            self.runner.run_patch(self.patch_content)
        self.assertIn(err_msg, str(ctx.exception))

    @patch("subprocess.run")
    def test_execute_command_success(self, mock_subprocess_run):
        expected_stdout = f"output_{uuid.uuid4().hex}"
        mock_result = MagicMock()
        mock_result.stdout = expected_stdout
        mock_subprocess_run.return_value = mock_result

        cmd = [uuid.uuid4().hex, uuid.uuid4().hex]
        timeout_val = random.randint(1, 100)

        output = self.runner.execute_command(cmd, timeout=timeout_val)

        self.assertEqual(output, expected_stdout)
        mock_subprocess_run.assert_called_once_with(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True,
            cwd=self.random_repo_path,
            timeout=timeout_val
        )

    @patch("subprocess.run")
    def test_execute_command_timeout(self, mock_subprocess_run):
        timeout_val = random.randint(1, 50)
        mock_subprocess_run.side_effect = subprocess.TimeoutExpired(cmd=uuid.uuid4().hex, timeout=timeout_val)

        cmd = [uuid.uuid4().hex]

        with self.assertRaises(PatchRunnerError) as ctx:
            self.runner.execute_command(cmd, timeout=timeout_val)
        self.assertIn(str(timeout_val), str(ctx.exception))

    @patch("subprocess.run")
    def test_execute_command_called_process_error(self, mock_subprocess_run):
        err_stderr = f"error_stderr_{uuid.uuid4().hex}"
        mock_subprocess_run.side_effect = subprocess.CalledProcessError(
            returncode=random.randint(1, 255),
            cmd=uuid.uuid4().hex,
            stderr=err_stderr
        )

        cmd = [uuid.uuid4().hex]

        with self.assertRaises(PatchRunnerError) as ctx:
            self.runner.execute_command(cmd)
        self.assertIn(err_stderr, str(ctx.exception))

    @patch("skills.patch_runner.PatchApplier")
    @patch("skills.patch_runner.PatchChecker")
    @patch("skills.patch_runner.PatchSanitizer")
    @patch("builtins.open")
    def test_run_patch_helper_function(self, mock_open, mock_sanitizer_cls, mock_checker_cls, mock_applier_cls):
        mock_file = mock_open.return_value.__enter__.return_value
        mock_file.read.return_value = self.patch_content

        expected_status = {uuid.uuid4().hex: uuid.uuid4().hex}

        mock_sanitizer = mock_sanitizer_cls.return_value
        mock_sanitizer.sanitize.return_value = uuid.uuid4().hex

        mock_checker = mock_checker_cls.return_value
        mock_checker.check.return_value = uuid.uuid4().hex

        mock_applier = mock_applier_cls.return_value
        mock_applier.apply.return_value = expected_status

        result = run_patch(self.random_patch_path, repo_path=self.random_repo_path)

        mock_open.assert_called_once_with(self.random_patch_path, "r", encoding="utf-8")
        self.assertEqual(result, expected_status)