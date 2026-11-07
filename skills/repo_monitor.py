import os
import subprocess


class GitCommitter:
    """Класс для выполнения Git-операций (добавление и коммит файлов) в репозитории."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def commit(self, message: str) -> bool:
        """Создает коммит с переданным сообщением в указанном репозитории."""
        cmd = ["git", "-C", self.repo_path, "commit", "-m", message]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            if isinstance(e, (FileNotFoundError, PermissionError)):
                return False
            return False

    def commit_changes(self, file_path: str, message: str) -> bool:
        """Добавляет файл в индекс и создает коммит."""
        try:
            # git add
            add_cmd = ["git", "-C", self.repo_path, "add", file_path]
            add_result = subprocess.run(add_cmd, capture_output=True, text=True)
            if add_result.returncode != 0:
                return False

            # git commit
            return self.commit(message)
        except Exception as e:
            if isinstance(e, (FileNotFoundError, PermissionError)):
                return False
            return False


class RepoMonitor:
    """Класс для мониторинга изменений в репозитории."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def check_status(self) -> str:
        """Проверяет статус репозитория через git status."""
        cmd = ["git", "-C", self.repo_path, "status", "--porcelain"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout
        except Exception as e:
            if isinstance(e, (FileNotFoundError, PermissionError)):
                return ""
            return ""
        return ""