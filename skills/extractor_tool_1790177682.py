import xml.etree.ElementTree as ET
import datetime
import uuid
import os
import json
import re
from typing import Any, Dict


class ExtractorTool:
    """
    Модуль для извлечения метаданных из различного вида разметки (XML, HTML, JSON, Frontmatter)
    и генерации отчетов об извлечении.
    """

    def __init__(self) -> None:
        self.extractor_version = "1.0.0-stable"

    def extract_metadata_from_markup(self, markup_data: str) -> Dict[str, Any]:
        """
        Извлекает метаданные из строки разметки.
        Поддерживает XML-структуры, HTML meta-теги, JSON script-блоки и YAML/Markdown frontmatter.
        """
        if not isinstance(markup_data, str):
            return {}

        metadata: Dict[str, Any] = {}

        # 1. Поиск Frontmatter: --- \n key: val \n ---
        frontmatter_match = re.search(
            r"^---\s*\n(.*?)\n---\s*\n", markup_data, re.DOTALL
        )
        if frontmatter_match:
            fm_content = frontmatter_match.group(1)
            for line in fm_content.split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    metadata[key.strip()] = val.strip().strip("\"'")

        # 2. Парсинг XML (<entry key="..." value="...">)
        xml_match = re.search(r"(<[a-zA-Z0-9_-]+.*>)", markup_data, re.DOTALL)
        if xml_match:
            try:
                root = ET.fromstring(xml_match.group(1).strip())
                for entry in root.findall(".//entry"):
                    key = entry.get("key")
                    val = entry.get("value")
                    if key is not None:
                        metadata[key] = val
            except ET.ParseError:
                pass

        # Резервный поиск <entry> через регулярные выражения
        entry_matches_1 = re.findall(
            r"<entry\s+[^>]*key=[\"']([^\"']+)[\"']\s+[^>]*value=[\"']([^\"']*)[\"']",
            markup_data,
            re.IGNORECASE,
        )
        for key, val in entry_matches_1:
            metadata[key] = val

        entry_matches_2 = re.findall(
            r"<entry\s+[^>]*value=[\"']([^\"']*)[\"']\s+[^>]*key=[\"']([^\"']+)[\"']",
            markup_data,
            re.IGNORECASE,
        )
        for val, key in entry_matches_2:
            metadata[key] = val

        # 3. Поиск HTML meta-тегов: <meta name="..." content="...">
        meta_tags = re.findall(
            r"<meta\s+name=[\"']([^\"']+)[\"']\s+content=[\"']([^\"']*)[\"']",
            markup_data,
            re.IGNORECASE,
        )
        for name, content in meta_tags:
            metadata[name] = content

        # 4. Поиск JSON script-блоков: <script type="application/json">...</script>
        json_blocks = re.findall(
            r"<script[^>]*type=[\"']application/json[\"'][^>]*>(.*?)</script>",
            markup_data,
            re.DOTALL | re.IGNORECASE,
        )
        for block in json_blocks:
            try:
                data = json.loads(block.strip())
                if isinstance(data, dict):
                    metadata.update(data)
            except (json.JSONDecodeError, TypeError):
                pass

        # Добавляем системные атрибуты
        metadata["processing_timestamp"] = datetime.datetime.now().isoformat()
        metadata["extractor_version"] = self.extractor_version
        metadata["operation_id"] = str(uuid.uuid4())

        return metadata

    def extract(self, markup_data: str) -> Dict[str, Any]:
        """Псевдоним для extract_metadata_from_markup."""
        return self.extract_metadata_from_markup(markup_data)

    def generate_extraction_report(self, markup_data: str, prefix: str) -> str:
        """
        Выполняет извлечение и сохраняет результат в текстовый файл-артефакт.
        Возвращает абсолютный путь к созданному файлу.
        """
        metadata = self.extract_metadata_from_markup(markup_data)
        filename = f"{prefix}_extraction_log.txt"
        file_path = os.path.abspath(filename)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("--- Extraction Report ---\n")
            for k, v in sorted(metadata.items()):
                f.write(f"{k}: {v}\n")
            f.write("--- End of Report ---\n")

        return file_path


def extract_metadata(markup_data: str) -> Dict[str, Any]:
    """Вспомогательная функция для быстрого извлечения метаданных."""
    tool = ExtractorTool()
    return tool.extract_metadata_from_markup(markup_data)
