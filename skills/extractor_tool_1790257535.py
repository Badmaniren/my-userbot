import json
import os
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import Any, Dict


class MetadataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.metadata = {}
        self.in_title = False
        self.title_data = []

    def handle_starttag(self, tag, attrs):
        attrs_dict = {k.lower(): v for k, v in attrs if v is not None}
        tag_lower = tag.lower()
        if tag_lower == 'title':
            self.in_title = True
            self.title_data = []
        elif tag_lower == 'meta':
            name = attrs_dict.get('name') or attrs_dict.get('property')
            content = attrs_dict.get('content')
            if name and content is not None:
                self.metadata[name] = content

    def handle_endtag(self, tag):
        if tag.lower() == 'title':
            self.in_title = False
            title_text = ''.join(self.title_data).strip()
            if title_text and 'title' not in self.metadata:
                self.metadata['title'] = title_text

    def handle_data(self, data):
        if self.in_title:
            self.title_data.append(data)


class ExtractorTool:
    """Модуль извлечения метаданных из разметки."""

    def extract(self, markup: str) -> Dict[str, Any]:
        """
        Извлекает метаданные из переданной разметки (HTML, XML, JSON script, Frontmatter).
        """
        if not isinstance(markup, str):
            return {}

        metadata: Dict[str, Any] = {}

        # 1. Frontmatter (YAML-подобная разметка)
        frontmatter_match = re.search(r"^\s*---\s*\n(.*?)\n\s*---\s*\n", markup, re.DOTALL)
        if frontmatter_match:
            fm_content = frontmatter_match.group(1)
            for line in fm_content.split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    metadata[key.strip()] = val.strip().strip("\"'")

        # 2. HTML Meta tags & Title
        try:
            parser = MetadataParser()
            parser.feed(markup)
            for k, v in parser.metadata.items():
                if k not in metadata:
                    metadata[k] = v
        except Exception:
            pass

        # Дополнительный regex поиск для meta тегов на случай сбоев HTMLParser
        meta_matches = re.findall(
            r"<meta\s+[^>]*?(?:name|property)=[\"']([^\"']+)[\"']\s+content=[\"']([^\"']*)[\"']",
            markup,
            re.IGNORECASE,
        )
        for name, content in meta_matches:
            if name not in metadata:
                metadata[name] = content

        meta_matches_reverse = re.findall(
            r"<meta\s+[^>]*?content=[\"']([^\"']*)[\"']\s+(?:name|property)=[\"']([^\"']+)[\"']",
            markup,
            re.IGNORECASE,
        )
        for content, name in meta_matches_reverse:
            if name not in metadata:
                metadata[name] = content

        # 3. JSON script blocks
        json_blocks = re.findall(
            r"<script[^>]*type=[\"']application/json[\"'][^>]*>(.*?)</script>",
            markup,
            re.DOTALL | re.IGNORECASE,
        )
        for block in json_blocks:
            try:
                data = json.loads(block.strip())
                if isinstance(data, dict):
                    for k, v in data.items():
                        if k not in metadata:
                            metadata[k] = v
            except (json.JSONDecodeError, TypeError):
                pass

        # 4. XML <entry> tags
        if "<entry" in markup.lower():
            try:
                cleaned = markup.strip()
                # Извлекаем XML корень если окаймлено тэгами
                if not cleaned.startswith("<"):
                    cleaned = f"<root>{cleaned}</root>"
                root = ET.fromstring(cleaned)
                for entry in root.findall(".//entry"):
                    key = entry.get("key") or entry.get("name")
                    val = entry.get("value") or entry.text
                    if key and val is not None:
                        metadata[key] = val.strip() if isinstance(val, str) else val
            except Exception:
                pass

        return metadata

    def extract_metadata_from_markup(self, markup: str) -> Dict[str, Any]:
        """Алиас для extract."""
        return self.extract(markup)

    def generate_extraction_report(self, markup_data: str, prefix: str) -> str:
        """
        Генерирует текстовый отчет об извлеченных метаданных и возвращает путь к файлу.
        """
        metadata = self.extract(markup_data)
        filename = f"{prefix}_extraction_report.txt"
        file_path = os.path.abspath(filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("--- Extraction Report ---\n")
            for k, v in metadata.items():
                f.write(f"{k}: {v}\n")
            f.write("--- End of Report ---\n")

        return file_path


def extract_metadata(markup: str) -> Dict[str, Any]:
    return ExtractorTool().extract(markup)


def extract(markup: str) -> Dict[str, Any]:
    return ExtractorTool().extract(markup)
