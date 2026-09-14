import io
import requests


class ErrorAnalyzer:
    """Анализатор логов и ошибок для предотвращения рекурсивных сбоев."""

    def analyze_file(self, filepath: str) -> bool:
        """Анализирует лог-файл на наличие критических ошибок.

        Бросает FileNotFoundError, если файл не найден.
        Перехватывает PermissionError и возвращает False.
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            raise
        except PermissionError:
            return False

        if not content:
            return False

        return self.parse_signature(content)

    def analyze_stream(self, url: str) -> bool:
        """Загружает лог из потока по URL и анализирует его."""
        response = requests.get(url, stream=True)
        data = response.raw.read()
        text_data = data.decode("utf-8", errors="ignore")
        return self.parse_signature(text_data)

    def parse_signature(self, line: str) -> bool:
        """Проверяет строку на наличие сигнатур ошибок."""
        error_keywords = [
            "ERROR",
            "CRITICAL",
            "FATAL",
            "Traceback",
            "NullPointerException",
        ]
        return any(keyword in line for keyword in error_keywords)

    def detect_recursion(self, history: list) -> bool:
        """Определяет наличие рекурсивных (повторяющихся) сбоев в истории."""
        if not history:
            return False
        # Проверяем, есть ли дублирующиеся элементы или слишком много одинаковых ошибок
        for item in set(history):
            if history.count(item) >= 3:
                return True
        return False


# Функции для интеграционных тестов


def analyze_error_log(filepath: str) -> str:
    """Интеграционная функция для чтения и возврата содержимого или описания

    ошибки из лога.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    return content


def is_recursive_failure(analysis_result: str) -> bool:
    """Интеграционная функция для проверки результата анализа на рекурсивность."""
    analyzer = ErrorAnalyzer()
    lines = analysis_result.splitlines()
    return analyzer.detect_recursion(lines)