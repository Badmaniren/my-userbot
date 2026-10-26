import re
from typing import Any, Dict


class ExtractorToolError(Exception):
    """Исключение при ошибках работы ExtractorTool."""
    pass


class ExtractorTool:
    """Инструмент извлечения метаданных из разметки."""

    def __init__(self, strict: bool = False, **kwargs: Any) -> None:
        self.strict = strict

    def __enter__(self) -> "ExtractorTool":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        pass

    def parse_attributes(self, tag_str: str) -> Dict[str, str]:
        """
        Разбирает строку атрибутов HTML/XML тега на словарь.
        """
        if not tag_str or not tag_str.strip():
            return {}

        # Регулярное выражение для захвата атрибутов с разными типами кавычек
        pattern = r'([^\s=/>]+)\s*=\s*(?:"([^"]*)"|\'([^\']*)\'|([^\s/>]+))'
        attributes: Dict[str, str] = {}

        for match in re.finditer(pattern, tag_str):
            key = match.group(1)
            # Выбираем захваченную группу в зависимости от типа кавычек
            val = match.group(2) if match.group(2) is not None else \
                  match.group(3) if match.group(3) is not None else \
                  match.group(4)
            attributes[key] = val

        return attributes

    def extract(self, markup: str) -> Dict[str, str]:
        """
        Извлекает метаданные (заголовок <title> и атрибуты <meta>) из разметки.
        """
        if not isinstance(markup, str):
            raise ExtractorToolError(f"Ожидалась строка, получен {type(markup).__name__}")

        result: Dict[str, str] = {}

        # Извлечение тега <title>
        title_match = re.search(r'<title(?:\s+[^>]*)?>(.*?)</title>', markup, re.IGNORECASE | re.DOTALL)
        if title_match:
            result['title'] = title_match.group(1).strip()

        # Извлечение тегов <meta>
        meta_matches = re.finditer(r'<meta\s+([^>]+)>', markup, re.IGNORECASE)
        for meta_match in meta_matches:
            attrs_str = meta_match.group(1)
            attrs = self.parse_attributes(attrs_str)

            content = attrs.get("content")
            if content is not None:
                # Приоритет ключей согласно стандартам мета-тегов
                key = attrs.get("name") or attrs.get("property") or attrs.get("http-equiv")
                if key:
                    result[key] = content

        return result
