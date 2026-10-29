import subprocess
import os
import logging
from skills.patch_applier import PatchApplier, PatchApplierError
from skills.patch_verifier import PatchVerifier, PatchVerifierError, PatchExecutor

logger = logging.getLogger(__name__)


class PatchPipelineRunner:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.applier = PatchApplier(repo_path)
        self.verifier = PatchVerifier(repo_path, executor=PatchExecutor(repo_path))

    def _ensure_git_repo(self):
        try:
            os.makedirs(self.repo_path, exist_ok=True)
        except OSError as e:
            logger.debug(f"Could not create directory {self.repo_path}: {e}")

        if not os.path.exists(self.repo_path):
            return

        git_dir = os.path.join(self.repo_path, ".git")
        is_git_repo = False
        if os.path.exists(git_dir):
            try:
                res = subprocess.run(
                    ["git", "-C", self.repo_path, "rev-parse", "--is-inside-work-tree"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                if res.returncode == 0 and res.stdout.strip() == "true":
                    is_git_repo = True
            except (subprocess.SubprocessError, OSError) as e:
                logger.debug(f"Git check failed: {e}")

        if not is_git_repo:
            try:
                subprocess.run(
                    ["git", "init"],
                    cwd=self.repo_path,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                )
                subprocess.run(
                    ["git", "config", "user.email", "test@test.com"],
                    cwd=self.repo_path,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                )
                subprocess.run(
                    ["git", "config", "user.name", "Test User"],
                    cwd=self.repo_path,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                )
                subprocess.run(
                    ["git", "add", "."],
                    cwd=self.repo_path,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                )
                subprocess.run(
                    ["git", "commit", "-m", "init", "--allow-empty"],
                    cwd=self.repo_path,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=False
                )
            except (subprocess.SubprocessError, OSError) as e:
                logger.debug(f"Git initialization failed: {e}")

    def _safe_rollback(self, backup_tag: str):
        try:
            self.applier.rollback(backup_tag)
        except (PatchApplierError, Exception) as e:
            logger.warning(f"Rollback to {backup_tag} failed: {e}")

    def execute(self, patch_data: dict, backup_tag: str = "default_backup") -> bool:
        if backup_tag == "default_backup" and isinstance(patch_data, dict) and "backup_tag" in patch_data:
            backup_tag = patch_data["backup_tag"]

        self._ensure_git_repo()
        try:
            if not self.applier.create_recovery_point(backup_tag):
                return False
        except (PatchApplierError, Exception) as e:
            logger.debug(f"Initial recovery point creation failed: {e}. Retrying after repo check.")
            self._ensure_git_repo()
            try:
                if not self.applier.create_recovery_point(backup_tag):
                    return False
            except (PatchApplierError, Exception) as err:
                logger.error(f"Recovery point creation failed: {err}")
                return False

        try:
            result = self.verifier.verify_and_apply(patch_data)
            if not result:
                self._safe_rollback(backup_tag)
                return False
            return True
        except (PatchApplierError, PatchVerifierError, Exception) as e:
            logger.error(f"Error during patch verification and application: {e}")
            self._safe_rollback(backup_tag)
            return False


def run_patch_pipeline(repo_path: str, patch_data: dict, backup_tag: str = "default_backup") -> bool:
    runner = PatchPipelineRunner(repo_path)
    return runner.execute(patch_data, backup_tag)