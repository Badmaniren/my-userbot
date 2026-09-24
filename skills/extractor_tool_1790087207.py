import xml.etree.ElementTree as ET
import datetime
import uuid
import os

class ExtractorTool:
    """
    Модуль для извлечения метаданных из XML-разметки и генерации отчетов.
    """

    def __init__(self):
        self.extractor_version = "1.0.4-stable"

    def extract_metadata_from_markup(self, markup_data: str) -> dict:
        """
        Парсит входящую разметку и извлекает ключи метаданных.
        Добавляет системные поля: timestamp, version и уникальный operation_id.
        """
        if not markup_data or not markup_data.strip().startswith('<'):
            return {}
        try:
            root = ET.fromstring(markup_data.strip())
        except Exception:
            return {}
        
        extracted_metadata = {}
        
        # Поиск всех элементов <entry> в структуре
        for entry in root.findall(".//entry"):
            key = entry.get("key")
            value = entry.get("value")
            if key is not None:
                extracted_metadata[key] = value
        
        # Генерация системных атрибутов для интеграционного следа
        extracted_metadata["processing_timestamp"] = datetime.datetime.now().isoformat()
        extracted_metadata["extractor_version"] = self.extractor_version
        extracted_metadata["operation_id"] = str(uuid.uuid4())
        
        return extracted_metadata

    def generate_extraction_report(self, markup_data: str, prefix: str) -> str:
        """
        Выполняет извлечение и сохраняет результат в текстовый файл-артефакт.
        Возвращает абсолютный путь к созданному файлу.
        """
        metadata = self.extract_metadata_from_markup(markup_data)
        
        # Формирование имени файла с использованием префикса
        filename = f"{prefix}_extraction_log.txt"
        file_path = os.path.abspath(filename)
        
        # Запись данных в файл для проверки тестом (обязательно наличие trace_id)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"--- Extraction Report ---\n")
            f.write(f"Operation ID: {metadata.get('operation_id')}\n")
            f.write(f"Timestamp: {metadata.get('processing_timestamp')}\n")
            f.write(f"Trace ID: {metadata.get('trace_id')}\n")
            f.write(f"Metric Value: {metadata.get('metric_val')}\n")
            f.write(f"Label: {metadata.get('label')}\n")
            f.write(f"Version: {metadata.get('extractor_version')}\n")
            f.write(f"--- End of Report ---\n")
            
        return file_path


def extractor_tool_1790087207(markup: str) -> dict:
    tool = ExtractorTool()
    return tool.extract_metadata_from_markup(markup)