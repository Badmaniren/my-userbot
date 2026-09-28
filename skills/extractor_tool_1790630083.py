import re
from typing import Any, Dict

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None


class ExtractorTool:
    """Модуль извлечения метаданных из HTML-разметки."""

    def __init__(self) -> None:
        pass

    def extract(self, html_content: str) -> Dict[str, Any]:
        """Извлекает метаданные из переданной HTML-разметки."""
        return extract_metadata(html_content)


def extract_metadata(html_content: str) -> Dict[str, Any]:
    """
    Извлекает метаданные из HTML-разметки.
    Ищет теги <meta> и возвращает словарь атрибутов 'name' и 'content'.
    """
    if not html_content or not isinstance(html_content, str):
        return {}

    metadata = {}
    if BeautifulSoup is not None:
        soup = BeautifulSoup(html_content, 'html.parser')
        meta_tags = soup.find_all('meta')

        for tag in meta_tags:
            name = tag.get('name')
            content = tag.get('content')
            if name and content:
                metadata[name] = content
    else:
        meta_tags = re.findall(
            r"<meta\s+name=[\"']([^\"']+)[\"']\s+content=[\"']([^\"']*)[\"']",
            html_content,
            re.IGNORECASE,
        )
        for name, content in meta_tags:
            metadata[name] = content

        meta_tags_rev = re.findall(
            r"<meta\s+content=[\"']([^\"']*)[\"']\s+name=[\"']([^\"']+)[\"']",
            html_content,
            re.IGNORECASE,
        )
        for content, name in meta_tags_rev:
            metadata[name] = content

    return metadata
