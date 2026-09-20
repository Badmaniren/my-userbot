import json
import csv
import io
import os

class PortfolioExporter:
    """Класс для экспорта портфельных отчетов и данных мониторинга в JSON и CSV форматы."""

    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def _normalize_data(self, data):
        """Приводит данные к стандартному словарю со списками записей по символам."""
        if not isinstance(data, dict):
            return data

        normalized = {}
        for symbol, records in data.items():
            if isinstance(records, list):
                normalized[symbol] = records
            else:
                normalized[symbol] = [records]
        return normalized

    def export_json(self, destination_file: str) -> bool:
        """Экспортирует данные хранилища в JSON файл."""
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            normalized_data = self._normalize_data(data)

            with open(destination_file, "w", encoding="utf-8") as f:
                json.dump(normalized_data, f, ensure_ascii=False, indent=4)
            return True
        except (FileNotFoundError, IOError, json.JSONDecodeError):
            return False

    def export_csv(self, destination_file: str) -> bool:
        """Экспортирует данные хранилища в CSV файл."""
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            normalized_data = self._normalize_data(data)

            with open(destination_file, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["symbol", "price", "timestamp"])

                if isinstance(normalized_data, dict):
                    for symbol, records in normalized_data.items():
                        if isinstance(records, list):
                            for record in records:
                                if isinstance(record, dict):
                                    writer.writerow([
                                        symbol,
                                        record.get("price", ""),
                                        record.get("timestamp", "")
                                    ])
                                else:
                                    writer.writerow([symbol, record, ""])
                        else:
                            writer.writerow([symbol, records, ""])
            return True
        except (FileNotFoundError, IOError, json.JSONDecodeError):
            return False

    def get_json_stream(self) -> io.BytesIO:
        """Возвращает поток с данными в формате JSON."""
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            normalized_data = self._normalize_data(data)
            output = json.dumps(normalized_data, ensure_ascii=False, indent=4)
        except (FileNotFoundError, json.JSONDecodeError, IOError):
            output = "{}"
        return io.BytesIO(output.encode("utf-8"))

    def get_csv_stream(self) -> io.BytesIO:
        """Возвращает поток с данными в формате CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["symbol", "price", "timestamp"])

        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            normalized_data = self._normalize_data(data)
            if isinstance(normalized_data, dict):
                for symbol, records in normalized_data.items():
                    if isinstance(records, list):
                        for record in records:
                            if isinstance(record, dict):
                                writer.writerow([
                                    symbol,
                                    record.get("price", ""),
                                    record.get("timestamp", "")
                                ])
                            else:
                                writer.writerow([symbol, record, ""])
                    else:
                        writer.writerow([symbol, records, ""])
        except (FileNotFoundError, json.JSONDecodeError, IOError):
            pass

        return io.BytesIO(output.getvalue().encode("utf-8"))


# Функции и класс для интеграционной совместимости
def export_to_json(storage_file: str, destination_file: str) -> bool:
    exporter = PortfolioExporter(storage_file)
    return exporter.export_json(destination_file)

def export_to_csv(storage_file: str, destination_file: str) -> bool:
    exporter = PortfolioExporter(storage_file)
    return exporter.export_csv(destination_file)

class MarketPortfolioExporter(PortfolioExporter):
    def export_data(self, destination_file: str):
        return self.export_json(destination_file)