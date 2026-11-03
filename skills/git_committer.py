import subprocess
import os
from typing import Optional

class GitCommitter:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def commit(self, message: str) -> bool:
        """
        Выполняет git add . и git commit -m message.
        Совместим с юнит-тестами, где вызывается commit(random_message).
        """
        try:
            # Сначала делаем git add
            add_result = subprocess.run(
                ["git", "-C", self.repo_path, "add", "."],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Затем git commit
            commit_result = subprocess.run(
                ["git", "-C", self.repo_path, "commit", "-m", message],
                capture_output=True,
                text=True,
                check=True
            )
            return commit_result.returncode == 0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            return False

    def commit_changes(self, file_path: str, message: str) -> bool:
        """
        Выполняет добавление конкретного файла и коммит.
        Совместим с интеграционными тестами.
        """
        try:
            # Проверяем существование файла относительно репозитория
            full_path = os.path.join(self.repo_path, file_path)
            if not os.path.exists(full_path):
                return False

            add_result = subprocess.run(
                ["git", "-C", self.repo_path, "add", file_path],
                capture_output=True,
                text=True,
                check=True
            )
            
            commit_result = subprocess.run(
                ["git", "-C", self.repo_path, "commit", "-m", message],
                capture_output=True,
                text=True,
                check=True
            )
            return commit_result.returncode == 0
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
            return False