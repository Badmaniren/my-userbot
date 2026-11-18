import os
import json
from skills.repo_logger import RepoLogger

class RepoHealthError(Exception):
    """Кастомное исключение для ошибок сбора метрик здоровья репозитория."""
    pass

class RepoHealthCollector:
    """Класс для сбора агрегированных метрик здоровья репозитория."""
    
    def __init__(self, repo_path: str = None):
        if repo_path is not None:
            self.logger = RepoLogger(repo_path)
        else:
            self.logger = None

    def collect_metrics(self, repo_path: str, session_id: str = None, expected_threshold: int = None) -> dict:
        """Собирает метрики здоровья репозитория, анализируя лог-файлы и используя аудитора."""
        if self.logger is None:
            self.logger = RepoLogger(repo_path)

        if not os.path.exists(repo_path):
            raise RepoHealthError(f"Путь репозитория не существует: {repo_path}")

        collected_data = {}
        if session_id:
            try:
                for fname in os.listdir(repo_path):
                    if session_id in fname and fname.endswith(".log"):
                        file_path = os.path.join(repo_path, fname)
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            collected_data["log_content"] = content
            except Exception as e:
                if isinstance(e, RepoHealthError):
                    raise
                raise RepoHealthError(f"Ошибка при чтении лог-файлов: {e}")

        result = {
            "status": "healthy",
            "repo_path": repo_path,
            "session_id": session_id,
            "metrics": collected_data
        }

        if expected_threshold is not None:
            result["threshold"] = expected_threshold

        if session_id:
            report_filename = os.path.join(repo_path, f"report_{session_id}.json")
            try:
                with open(report_filename, "w", encoding="utf-8") as f:
                    json.dump(result, f, ensure_ascii=False, indent=4)
            except Exception as e:
                if isinstance(e, RepoHealthError):
                    raise
                raise RepoHealthError(f"Ошибка при записи отчета: {e}")

        return result