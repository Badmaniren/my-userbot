"""
Модуль извлечения метаданных из разметки.
"""

import re
from typing import Dict, Any


class ExtractorTool:
    """Инструмент для извлечения метаданных из текстовой разметки."""

    def __init__(self) -> None:
        self.version = "1.0.0"

    def parse_attributes(self, tag_string: str) -> Dict[str, str]:
        """Извлекает атрибуты из строки тега."""
        if not tag_string or not isinstance(tag_string, str):
            return {}

        attributes: Dict[str, str] = {}
        pattern = r'([a-zA-Z0-9_-]+)="([^"]*)"|([a-zA-Z0-9_-]+)=\'([^\']*)\'|([a-zA-Z0-9_-]+)=([^\s>]+)'
        for match in re.finditer(pattern, tag_string):
            groups = match.groups()
            if groups[0] is not None:
                attributes[groups[0]] = groups[1]
            elif groups[2] is not None:
                attributes[groups[2]] = groups[3]
            elif groups[4] is not None:
                attributes[groups[4]] = groups[5]

        return attributes

    def extract(self, markup: str) -> Dict[str, Any]:
        """
        Извлекает метаданные из переданной строки разметки.
        Поддерживает парсинг тегов и их атрибутов.
        """
        if not markup or not isinstance(markup, str):
            raise ValueError("Разметка должна быть непустой строкой")

        markup_str = markup.strip()

        # 1. Пробуем парсить парный тег: <tag attrs>content</tag>
        pair_pattern = r'^<([a-zA-Z0-9_-]+)([^>]*)>(.*?)</[a-zA-Z0-9_-]+>$'
        match = re.match(pair_pattern, markup_str, re.DOTALL)
        if match:
            tag, attr_str, content = match.groups()
            res: Dict[str, Any] = {"tag": tag, "content": content}
            res.update(self.parse_attributes(attr_str))
            return res

        # 2. Пробуем парсить одиночный/самозакрывающийся тег: <tag attrs /> или <tag attrs>
        single_pattern = r'^<([a-zA-Z0-9_-]+)([^>]*?)/?>$'
        match = re.match(single_pattern, markup_str, re.DOTALL)
        if match:
            tag, attr_str = match.groups()
            res = {"tag": tag, "content": ""}
            res.update(self.parse_attributes(attr_str))
            return res

        raise ValueError(f"Некорректный формат разметки: {markup}")
