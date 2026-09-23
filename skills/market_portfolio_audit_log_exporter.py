import json
import os
from skills.market_parser import MarketParser


class PortfolioAuditLogExporter:
    """Модуль для экспорта аудита портфельных операций и логов."""

    def __init__(self, storage_file: str):
        self.storage_file = storage_file

    def _read_storage(self):
        try:
            if not os.path.exists(self.storage_file):
                return []
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if not content.strip():
                    return []
                return json.loads(content)
        except (IOError, json.JSONDecodeError, UnicodeDecodeError):
            # Перехватываем для безопасного возврата ошибки наружу в логике экспорта/сумм
            raise

    def export_audit_logs(self, export_path: str) -> bool:
        try:
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = f.read()
                    if not data.strip():
                        data = "{}"
                    else:
                        json.loads(data)
            except (FileNotFoundError, OSError):
                if isinstance(self.storage_file, str) and not os.path.exists(self.storage_file):
                    with open(export_path, 'w', encoding='utf-8') as f:
                        f.write("{}")
                    return True
                raise

            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(data)
            return True
        except Exception:
            return False

    def get_audit_stream_summary(self) -> dict:
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                content = f.read()
                data = json.loads(content)
                if not isinstance(data, list):
                    data = [data]
                return {"total_records": len(data)}
        except Exception:
            return {"total_records": 0}

    def verify_log_integrity(self) -> bool:
        try:
            with open(self.storage_file, 'r', encoding='utf-8') as f:
                json.load(f)
            return True
        except Exception:
            return False


class MarketPortfolioAuditLogExporter(PortfolioAuditLogExporter):
    """Класс-адаптер для интеграционных тестов с поддержкой альтернативных имен методов."""

    def generate_audit_log(self, export_path: str):
        return self.export_audit_logs(export_path)

    def process_audit_stream(self, export_path: str):
        return self.export_audit_logs(export_path)