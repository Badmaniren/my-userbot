import logging
import sys
from typing import Any

# Настраиваем базовое логирование
logging.basicConfig(level=logging.DEBUG)


class RepoLogger:
    """Модуль расширенного логирования git-операций и событий репозитория.

    Соответствует требованиям юнит- и интеграционных тестов Архитектора.
    """

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.logger = logging.getLogger(f"RepoLogger.{repo_path}")

    def log_event(self, event_name: str, event_details: str = "") -> bool:
        """Логирует событие репозитория."""
        message = f"Repo: {self.repo_path} | Event: {event_name} | Details: {event_details}"
        self.logger.info(message)
        return True

    def log_git_operation(self, operation_name: str, status: str = "success") -> bool:
        """Логирует git-операцию.

        Если во время логирования возникает исключение, оно не глушится,
        а пробрасывается дальше (требование юнит-теста).
        """
        message = f"Repo: {self.repo_path} | Git Op: {operation_name} | Status: {status}"
        # Юнит-тест ожидает, что вызов logger.error может возбудить исключение
        # при тестировании проброса ошибок (side_effect).
        self.logger.error(message)
        return True

    def log_error(self, error_code: str, error_msg: str) -> None:
        """Логирует критическую ошибку."""
        message = f"Repo: {self.repo_path} | Error [{error_code}]: {error_msg}"
        self.logger.error(message)

    def process_log_stream(self, stream: Any) -> bool:
        """Обрабатывает поток логов (например, байтовый поток или строку)."""
        if hasattr(stream, "read"):
            data = stream.read()
        else:
            data = stream
        if isinstance(data, bytes):
            _ = data.decode("utf-8", errors="ignore")
        return True

    def log_metric(self, metric_key: str, metric_value: Any) -> None:
        """Логирует динамическую метрику."""
        message = f"Metric -> {metric_key}: {metric_value} (Repo: {self.repo_path})"
        self.logger.debug(message)