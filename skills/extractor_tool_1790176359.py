import json
import re
import xml.etree.ElementTree as ET
import datetime
import uuid
import os
from typing import Any, Dict


class ExtractorTool:
    """
    Модуль для извлечения метаданных из XML/HTML разметки и генерации отчетов.
    """

    def __init__(self) -> None:
        self.extractor_version = "1.0.4-stable"

    def extract_metadata_from_markup(self, markup_data: str) -> Dict[str, Any]:
        """
        Парсит входящую разметку и извлекает ключи метаданных.
        Добавляет системные поля: processing_timestamp, extractor_version и уникальный operation_id.
        """
        extracted_metadata: Dict[str, Any] = {}

        if not isinstance(markup_data, str) or not markup_data.strip():
            extracted_metadata["processing_timestamp"] = datetime.datetime.now().isoformat()
            extracted_metadata["extractor_version"] = self.extractor_version
            extracted_metadata["operation_id"] = str(uuid.uuid4())
            return extracted_metadata

        # Парсинг XML разметки с <entry key="..." value="...">
        try:
            root = ET.fromstring(markup_data.strip())
            for entry in root.findall(".//entry"):
                key = entry.get("key")
                value = entry.get("value")
                if key is not None:
                    extracted_metadata[key] = value

            if not extracted_metadata:
                for elem in root.iter():
                    if elem.tag and elem.text and elem.text.strip():
                        extracted_metadata[elem.tag] = elem.text.strip()
                    for attr_k, attr_v in elem.attrib.items():
                        extracted_metadata[f"{elem.tag}_{attr_k}"] = attr_v
        except ET.ParseError:
            pass

        # Поиск <meta name="..." content="...">
        meta_tags = re.findall(
            r"<meta\s+name=[\"']([^\"']+)[\"']\s+content=[\"']([^\"']*)[\"']",
            markup_data,
            re.IGNORECASE,
        )
        for name, content in meta_tags:
            extracted_metadata[name] = content

        # Поиск блоков JSON внутри <script type="application/json">
        json_blocks = re.findall(
            r"<script[^>]*type=[\"']application/json[\"'][^>]*>(.*?)</script>",
            markup_data,
            re.DOTALL | re.IGNORECASE,
        )
        for block in json_blocks:
            try:
                data = json.loads(block.strip())
                if isinstance(data, dict):
                    extracted_metadata.update(data)
            except (json.JSONDecodeError, TypeError):
                pass

        # Поиск Frontmatter (между ---)
        frontmatter_match = re.search(
            r"^---\s*\n(.*?)\n---\s*\n", markup_data, re.DOTALL
        )
        if frontmatter_match:
            fm_content = frontmatter_match.group(1)
            for line in fm_content.split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    extracted_metadata[key.strip()] = val.strip().strip("\"'")

        # Системные метаданные
        extracted_metadata["processing_timestamp"] = datetime.datetime.now().isoformat()
        extracted_metadata["extractor_version"] = self.extractor_version
        extracted_metadata["operation_id"] = str(uuid.uuid4())

        return extracted_metadata

    def extract(self, markup: str) -> Dict[str, Any]:
        """Алиас метода извлечения метаданных."""
        return self.extract_metadata_from_markup(markup)

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
            f.write(f"Operation ID: {metadata.get('operation_id')}\n")
            f.write(f"Timestamp: {metadata.get('processing_timestamp')}\n")
            f.write(f"Trace ID: {metadata.get('trace_id')}\n")
            f.write(f"Metric Value: {metadata.get('metric_val')}\n")
            f.write(f"Label: {metadata.get('label')}\n")
            f.write(f"Version: {metadata.get('extractor_version')}\n")
            f.write("--- End of Report ---\n")

        return file_path


def extract_metadata(markup: str) -> Dict[str, Any]:
    """Вспомогательная функция для извлечения метаданных."""
    tool = ExtractorTool()
    return tool.extract(markup)
