"""
Модуль извлечения метаданных из разметки.
Соответствует требованиям Архитектора и правилам кодирования Унги.
"""

import re
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional, Union


class MetadataExtractionError(Exception):
    """Исключение при ошибках извлечения метаданных."""
    pass


class ExtractorToolError(MetadataExtractionError):
    """Базовое исключение инструмента extractor_tool_1792686109."""
    pass


class MetadataExtractor:
    """Базовый класс извлечения метаданных."""

    def __init__(self, options: Optional[Dict[str, Any]] = None) -> None:
        self.options = options or {}

    def extract_metadata(self, markup: str) -> Dict[str, Any]:
        """Извлекает метаданные из строки разметки."""
        if not markup or not isinstance(markup, str):
            return {}

        metadata: Dict[str, Any] = {}

        # Извлечение тегов <meta name="..." content="..."> или <meta property="..." content="...">
        meta_pattern = r'<meta\s+(?:name|property)=["\']([^"\']+)["\']\s+content=["\']([^"\']*)["\']\s*/?>'
        for match in re.finditer(meta_pattern, markup, re.IGNORECASE):
            key, val = match.groups()
            metadata[key.strip()] = val.strip()

        # Поиск пар ключ-значение формата Key: Value или Key=Value
        kv_pattern = r'^(?!\s*<)([a-z0-9_-]+)\s*[:=]\s*(.+)$'
        for line in markup.splitlines():
            match = re.match(kv_pattern, line.strip(), re.IGNORECASE)
            if match:
                key, value = match.groups()
                key_lower = key.lower()
                if key_lower not in metadata:
                    metadata[key_lower] = value.strip()

        return metadata


class ExtractorTool(MetadataExtractor):
    """Инструмент для извлечения метаданных из разметки и файлов."""

    def __init__(self, options: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(options=options)
        self.version = "1.0.0"

    def extract(self, markup: str) -> Dict[str, Any]:
        """Универсальный метод извлечения метаданных из разметки."""
        return self.extract_metadata(markup)

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

    def extract_tags(self, markup: str, tag_name: str) -> List[Dict[str, Any]]:
        """Извлекает список тегов с их атрибутами и содержимым."""
        if not markup or not tag_name or not isinstance(markup, str):
            return []

        results: List[Dict[str, Any]] = []
        pattern = rf'<{tag_name}(\s+[^>]*)?>(.*?)</{tag_name}>'
        matches = re.findall(pattern, markup, re.IGNORECASE | re.DOTALL)

        for attrs_str, content in matches:
            attrs = self.parse_attributes(attrs_str) if attrs_str else {}
            results.append({
                "tag": tag_name,
                "attributes": attrs,
                "content": content.strip()
            })

        return results

    def extract_from_file(self, filepath: str) -> Dict[str, Any]:
        """Извлекает метаданные из файла."""
        if not filepath:
            raise ExtractorToolError("Путь к файлу не может быть пустым")

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.extract(content)
        except Exception as e:
            if isinstance(e, ExtractorToolError):
                raise
            raise ExtractorToolError(f"Ошибка при чтении файла {filepath}: {e}") from e


def extract_metadata(markup: str) -> Dict[str, Any]:
    """Вспомогательная функция для быстрого извлечения метаданных."""
    extractor = ExtractorTool()
    return extractor.extract(markup)
