"""
Модуль извлечения метаданных из разметки.
"""

import re
from typing import Dict, Any, Optional


class ExtractorTool:
    """Модуль извлечения метаданных из разметки."""

    def __init__(self) -> None:
        self.version = "1.0.0"

    def parse_attributes(self, tag_string: str) -> Dict[str, str]:
        """Извлекает атрибуты из строки тега."""
        if not tag_string or not isinstance(tag_string, str):
            return {}

        attributes: Dict[str, str] = {}
        pattern = r'([a-zA-Z0-9_-]+)=["\']([^"\']*)["\']'
        matches = re.findall(pattern, tag_string)
        for key, value in matches:
            attributes[key] = value

        return attributes

    def extract(self, markup: str) -> Dict[str, Any]:
        """
        Извлекает метаданные из переданной строки разметки.
        Поддерживает атрибуты тегов и парсинг пар Ключ: Значение.
        """
        if not markup or not isinstance(markup, str):
            return {}

        metadata: Dict[str, Any] = {}

        # Извлечение атрибутов из всех тегов в разметке
        tag_pattern = r'<[^>]+>'
        tags = re.findall(tag_pattern, markup)
        for tag in tags:
            attrs = self.parse_attributes(tag)
            metadata.update(attrs)

        # Парсинг строк формата Key: Value
        key_val_pattern = r"(?i)^([a-z0-9_-]+):\s*(.+)$"
        for line in markup.splitlines():
            match = re.match(key_val_pattern, line.strip())
            if match:
                key, value = match.groups()
                metadata[key.lower()] = value.strip()

        return metadata
