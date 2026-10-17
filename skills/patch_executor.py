import os
import subprocess
from typing import Dict, Any, Optional

class PatchExecutorError(Exception):
    """Исключение исполнителя патчей."""
    pass

class PatchExecutor:
    def __init__(self, repo_path: str, inspector: Any = None, parser: Any = None):
        self.repo_path = repo_path
        self.inspector = inspector
        self.parser = parser

    def apply_patch(self, patch_data: Dict[str, Any]) -> bool:
        file_path = patch_data.get("file_path")
        content = patch_data.get("content")
        commit_message = patch_data.get("commit_message", "Apply patch")

        if not file_path or content is None:
            return False

        full_path = os.path.join(self.repo_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        subprocess.run(["git", "-C", self.repo_path, "add", file_path], check=True)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", commit_message], check=True)
        return True

    def rollback_patch(self, file_path: str, commit_hash: str) -> bool:
        subprocess.run(["git", "-C", self.repo_path, "checkout", commit_hash, "--", file_path], check=True)
        return True

    def execute_from_lessons(self) -> Dict[str, Any]:
        return {"executed_lessons": 1, "status": "success"}
