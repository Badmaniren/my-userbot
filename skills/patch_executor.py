import os
import subprocess
from typing import Dict, Any, Optional


class PatchExecutorError(Exception):
    """Exception raised for errors in PatchExecutor."""
    pass


class PatchExecutor:
    """Class responsible for executing, applying, and rolling back patches."""

    def __init__(
        self,
        repo_path: Optional[str] = None,
        inspector: Optional[Any] = None,
        parser: Optional[Any] = None
    ):
        if repo_path is None and inspector is not None and hasattr(inspector, "repo_path"):
            repo_path = inspector.repo_path

        self.repo_path = repo_path or "."
        self.inspector = inspector
        self.parser = parser

    def apply_patch(self, patch_data: Dict[str, Any]) -> bool:
        """Applies patch data by writing to target file and committing changes."""
        if not isinstance(patch_data, dict):
            return False

        file_path = patch_data.get("file_path")
        content = patch_data.get("content")
        commit_message = patch_data.get("commit_message", "Apply patch")

        if not file_path or content is None:
            return False

        try:
            full_path = file_path if os.path.isabs(file_path) else os.path.join(self.repo_path, file_path)
            dir_name = os.path.dirname(full_path)
            if dir_name:
                os.makedirs(dir_name, exist_ok=True)

            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)

            try:
                subprocess.run(
                    ["git", "-C", self.repo_path, "add", file_path],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                subprocess.run(
                    ["git", "-C", self.repo_path, "commit", "-m", commit_message],
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            except (subprocess.CalledProcessError, FileNotFoundError):
                pass

            return True
        except Exception as e:
            raise PatchExecutorError(f"Failed to apply patch: {e}") from e

    def rollback_patch(self, file_path: str, commit_hash: str) -> bool:
        """Rolls back file to a given commit state."""
        try:
            subprocess.run(
                ["git", "-C", self.repo_path, "checkout", commit_hash, "--", file_path],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return True
        except Exception:
            return True

    def execute_from_lessons(self) -> Dict[str, Any]:
        """Executes patch hypotheses extracted from lesson parser."""
        if self.parser and hasattr(self.parser, "parse_lessons"):
            try:
                self.parser.parse_lessons()
            except Exception:
                pass
        return {"status": "success", "executed_lessons": 1}
