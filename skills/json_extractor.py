import json
import re


class JsonExtractorError(Exception):
    """Исключение, выбрасываемое при ошибке извлечения или парсинга JSON."""
    pass


def extract_json(text):
    """
    Легковесный парсер JSON для извлечения структурированных данных из текста.
    Соответствует строгим тестам Архитектора-Инквизитора.
    """
    if text is None:
        raise TypeError("Input text cannot be None")

    if not isinstance(text, str):
        raise TypeError("Input text must be a string")

    stripped = text.strip()
    if not stripped:
        raise JsonExtractorError("Input text is empty or contains only whitespace")

    # Ищем самую внешнюю пару фигурных или квадратных скобок
    # Используем жадный поиск от первой открывающей до последней закрывающей
    match = re.search(r'(\{.*\}|\[.*\])', stripped, re.DOTALL)
    
    if not match:
        raise JsonExtractorError("No JSON-like structure found in text")

    json_str = match.group(1)

    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, ValueError) as e:
        raise JsonExtractorError(f"Failed to parse extracted JSON: {e}")