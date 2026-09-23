import json
import re
from typing import Any, Dict, Optional


class ExtractorTool:
    """Модуль извлечения метаданных из разметки."""

    def __init__(self) -> None:
        pass

    def extract(self, markup: str) -> Dict[str, Any]:
        """Извлекает метаданные из переданной разметки."""
        if not isinstance(markup, str):
            return {}

        metadata: Dict[str, Any] = {}

        # Ищем метаданные в тегах <meta> (например, HTML-подобная разметка)
        meta_tags = re.findall(
            r"<meta\s+name=[\"']([^\"']+)[\"']\s+content=[\"']([^\"']*)[\"']",
            markup,
            re.IGNORECASE,
        )
        for name, content in meta_tags:
            metadata[name] = content

        # Ищем блок JSON в тегах <script type="application/json"> или аналогичных
        json_blocks = re.findall(
            r"<script[^>]*type=[\"']application/json[\"'][^>]*>(.*?)</script>",
            markup,
            re.DOTALL | re.IGNORECASE,
        )
        for block in json_blocks:
            try:
                data = json.loads(block.strip())
                if isinstance(data, dict):
                    metadata.update(data)
            except (json.JSONDecodeError, TypeError):
                pass

        # Ищем заголовки (например, Markdown Frontmatter или простые ключи)
        frontmatter_match = re.search(
            r"^---\s*\n(.*?)\n---\s*\n", markup, re.DOTALL
        )
        if frontmatter_match:
            fm_content = frontmatter_match.group(1)
            for line in fm_content.split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    metadata[key.strip()] = val.strip().strip("\"'")

        return metadata


def extract_metadata(markup: str) -> Dict[str, Any]:
    """Вспомогательная функция для быстрой инициализации и извлечения."""
    tool = ExtractorTool()
    return tool.extract(markup)


ExtractorTool1790102839 = ExtractorTool
