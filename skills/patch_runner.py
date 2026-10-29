import subprocess
from skills.patch_sanitizer import PatchSanitizer
from skills.patch_checker import PatchChecker
from skills.patch_applier import PatchApplier

class PatchRunnerError(Exception):
    """Custom exception for PatchRunner errors."""
    pass

class PatchRunner:
    def __init__(self, repo_path=None):
        self.repo_path = repo_path

    def run_patch(self, patch_content):
        try:
            sanitizer = PatchSanitizer()
            sanitized_data = sanitizer.sanitize(patch_content)
        except Exception as e:
            if isinstance(e, PatchRunnerError):
                raise
            raise PatchRunnerError(f"Sanitization failed: {e}")

        try:
            checker = PatchChecker(repo_path=self.repo_path)
            check_result = checker.check(sanitized_data)
        except Exception as e:
            if isinstance(e, PatchRunnerError):
                raise
            raise PatchRunnerError(f"Checker failed: {e}")

        try:
            applier = PatchApplier(repo_path=self.repo_path) if self.repo_path else PatchApplier()
            applied_status = applier.apply(sanitized_data, self.repo_path)
        except Exception as e:
            if isinstance(e, PatchRunnerError):
                raise
            raise PatchRunnerError(f"Applier failed: {e}")

        return applied_status

    def execute_command(self, cmd, timeout=None):
        try:
            kwargs = {
                "stdout": subprocess.PIPE,
                "stderr": subprocess.PIPE,
                "text": True,
                "check": True
            }
            if self.repo_path:
                kwargs["cwd"] = self.repo_path
            if timeout is not None:
                kwargs["timeout"] = timeout

            result = subprocess.run(cmd, **kwargs)
            return result.stdout
        except subprocess.TimeoutExpired as e:
            raise PatchRunnerError(f"Command timed out after {timeout} seconds: {e}")
        except subprocess.CalledProcessError as e:
            raise PatchRunnerError(f"Command failed with stderr: {e.stderr}")
        except Exception as e:
            if isinstance(e, PatchRunnerError):
                raise
            raise PatchRunnerError(f"Command execution error: {e}")

def run_patch(patch_file_path, repo_path=None):
    with open(patch_file_path, "r", encoding="utf-8") as f:
        patch_content = f.read()
    runner = PatchRunner(repo_path=repo_path)
    return runner.run_patch(patch_content)