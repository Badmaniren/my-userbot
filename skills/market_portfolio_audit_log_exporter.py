import json
import os
from skills.market_parser import MarketParser


class PortfolioAuditLogExporter:
    """Модуль для экспорта аудита портфельных операций и логов."""

    def __init__(self, storage_file: str = "audit_log.json"):
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

    def process_log_file(self, log_path: str):
        records = []
        if not log_path or not os.path.exists(log_path):
            return records
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return records
            try:
                data = json.loads(content)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return [data]
            except json.JSONDecodeError:
                pass
            for line in content.splitlines():
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return records

    def export_audit_logs(self, export_path: str) -> bool:
        try:
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = f.read()
                    if not data.strip():
                        data = "{}"
                    else:
                        json.loads(data)
            except (IOError, FileNotFoundError):
                data = "{}"

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


market_portfolio_audit_log_exporter = MarketPortfolioAuditLogExporter
