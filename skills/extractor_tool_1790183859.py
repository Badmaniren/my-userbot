import json
import os
import re
from typing import Any, Dict, Optional


class ExtractorTool:
    """Инструмент для извлечения метаданных из разметки и файлов."""

    def __init__(self) -> None:
        pass

    def extract_metadata_from_markup(self, markup: str) -> Dict[str, Any]:
        """Извлекает словарь метаданных из строки разметки."""
        if not isinstance(markup, str):
            return {"metadata": {}}

        metadata: Dict[str, Any] = {}

        # 1. Frontmatter (--- ... ---)
        frontmatter_match = re.search(
            r"^---\s*\n(.*?)\n---(?:\s*\n|$)", markup, re.DOTALL
        )
        if frontmatter_match:
            fm_text = frontmatter_match.group(1)
            for line in fm_text.splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip()
                    val = val.strip().strip("\"'")
                    if val.isdigit():
                        val = int(val)
                    elif val.lower() == "true":
                        val = True
                    elif val.lower() == "false":
                        val = False
                    metadata[key] = val

        # 2. HTML <meta> tags
        meta_tags = re.finditer(r"<meta\s+([^>]+)>", markup, re.IGNORECASE)
        for tag_match in meta_tags:
            tag_str = tag_match.group(1)
            name_match = re.search(
                r'(?:name|property|http-equiv)=["\']([^"\']*)["\']',
                tag_str,
                re.IGNORECASE,
            )
            content_match = re.search(
                r'content=["\']([^"\']*)["\']', tag_str, re.IGNORECASE
            )
            if name_match and content_match:
                key = name_match.group(1)
                val = content_match.group(1)
                if val.isdigit():
                    val = int(val)
                metadata[key] = val

        # 3. Structured HTML Comments (<!-- metadata: {...} -->)
        comment_matches = re.finditer(
            r"<!--\s*metadata:\s*(\{.*?\})\s*-->", markup, re.DOTALL | re.IGNORECASE
        )
        for c_match in comment_matches:
            try:
                comment_json = json.loads(c_match.group(1))
                if isinstance(comment_json, dict):
                    metadata.update(comment_json)
            except Exception:
                pass

        # 4. <script type="application/json"> blocks
        script_matches = re.finditer(
            r"<script[^>]*type=[\"']application/json[\"'][^>]*>(.*?)</script>",
            markup,
            re.DOTALL | re.IGNORECASE,
        )
        for s_match in script_matches:
            try:
                script_json = json.loads(s_match.group(1).strip())
                if isinstance(script_json, dict):
                    metadata.update(script_json)
            except Exception:
                pass

        # 5. XML <entry key="..." value="..."> tags
        entry_matches = re.finditer(r"<entry\s+([^>]+)>", markup, re.IGNORECASE)
        for e_match in entry_matches:
            e_str = e_match.group(1)
            key_match = re.search(r'key=["\']([^"\']*)["\']', e_str, re.IGNORECASE)
            val_match = re.search(r'value=["\']([^"\']*)["\']', e_str, re.IGNORECASE)
            if key_match and val_match:
                metadata[key_match.group(1)] = val_match.group(1)

        return {"metadata": metadata}

    def extract_metadata(self, markup: str) -> Dict[str, Any]:
        """Алиас для extract_metadata_from_markup."""
        return self.extract_metadata_from_markup(markup)

    def extract(self, markup: str) -> Dict[str, Any]:
        """Возвращает словарь извлеченных метаданных."""
        res = self.extract_metadata_from_markup(markup)
        return res.get("metadata", {})

    def extract_metadata_from_file(self, filepath: str) -> Dict[str, Any]:
        """Извлекает метаданные из указанного файла."""
        if not os.path.exists(filepath):
            return {"metadata": {}, "source_file": filepath, "error": "File not found"}

        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        res = self.extract_metadata_from_markup(content)
        res["source_file"] = filepath
        return res


def extract_metadata(markup: str) -> Dict[str, Any]:
    """Верхнеуровневая функция для извлечения метаданных из разметки."""
    tool = ExtractorTool()
    return tool.extract_metadata(markup)


def extract_metadata_from_file(filepath: str) -> Dict[str, Any]:
    """Верхнеуровневая функция для извлечения метаданных из файла."""
    tool = ExtractorTool()
    return tool.extract_metadata_from_file(filepath)
