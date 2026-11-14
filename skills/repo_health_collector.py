import os
import json

class RepoHealthError(Exception):
    """Кастомное исключение для ошибок сбора метрик здоровья репозитория."""
    pass

class RepoHealthCollector:
    """Класс для сбора агрегированных метрик здоровья репозитория."""
    
    def __init__(self):
        pass

    def collect_metrics(self, repo_path: str, session_id: str = None, expected_threshold: int = None) -> dict:
        """Собирает метрики здоровья репозитория, анализируя лог-файлы и используя аудитора."""
        if not os.path.exists(repo_path):
            raise RepoHealthError(f"Путь репозитория не существует: {repo_path}")

        collected_data = {}
        if session_id:
            for fname in os.listdir(repo_path):
                if session_id in fname and fname.endswith(".log"):
                    file_path = os.path.join(repo_path, fname)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                            collected_data["log_content"] = content
                    except Exception as e:
                        raise RepoHealthError(f"Ошибка чтения лог-файла: {e}")

        report = {
            "status": "healthy",
            "session_id": session_id,
            "repo_path": repo_path,
            "metrics": collected_data
        }

        if expected_threshold is not None:
            report["threshold"] = expected_threshold

        if session_id:
            report_file_path = os.path.join(repo_path, f"report_{session_id}.json")
            try:
                with open(report_file_path, "w", encoding="utf-8") as f:
                    json.dump(report, f)
            except Exception as e:
                raise RepoHealthError(f"Ошибка записи файла отчета: {e}")

        return report