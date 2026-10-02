import json
import os
import csv
from skills.market_parser import MarketParser


class PortfolioAuditLogExporter:
    """Модуль для экспорта аудита портфельных операций и логов."""

    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def _read_storage(self):
        if not os.path.exists(self.storage_file):
            return []
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    return []
                return json.loads(content)
        except Exception:
            return []

    def export_audit_logs(self, export_path: str) -> bool:
        if not os.path.exists(self.storage_file):
            return False
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                data = f.read()
                # Проверка на валидность JSON
                json.loads(data)
        except Exception:
            return False

        with open(export_path, 'w', encoding='utf-8') as f:
            f.write(data)
        return True

    def get_audit_stream_summary(self) -> dict:
        if not os.path.exists(self.storage_file):
            return {"total_records": 0}
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    return {"total_records": 0}
                data = json.loads(content)
                if not isinstance(data, list):
                    data = [data]
                return {"total_records": len(data)}
        except Exception:
            return {"total_records": 0}

    def verify_log_integrity(self) -> bool:
        if not os.path.exists(self.storage_file):
            return False
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except Exception:
            return False

    def export_aggregated_report(self, export_path: str, format_type: str = "json") -> bool:
        data = self._read_storage()
        if not isinstance(data, list):
            data = [data]

        if format_type.lower() == "json":
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            return True
        elif format_type.lower() == "csv":
            if not data:
                with open(export_path, 'w', encoding='utf-8', newline='' ) as f:
                    pass
                return True
            
            fieldnames = set()
            for row in data:
                if isinstance(row, dict):
                    fieldnames.update(row.keys())
            fieldnames = sorted(list(fieldnames))

            with open(export_path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for row in data:
                    if isinstance(row, dict):
                        writer.writerow(row)
            return True
        return False


class MarketPortfolioAuditLogExporter(PortfolioAuditLogExporter):
    """Класс-адаптер для интеграционных тестов с поддержкой альтернативных имен методов."""

    def generate_audit_log(self, export_path: str):
        return self.export_audit_logs(export_path)

    def process_audit_stream(self, export_path: str):
        return self.export_audit_logs(export_path)