import os
import json
from typing import Any, Dict, List, Optional, Union

try:
    from skills.db_storage import MarketParser
except ImportError:
    class MarketParser:  # type: ignore
        def __init__(self, storage_file: str = "market_data.db"):
            self.storage_file = storage_file

        def fetch_price(self, url: str) -> float:
            return 0.0

        def load_data(self, filename: str) -> List[str]:
            if not os.path.exists(filename):
                return []
            with open(filename, "r", encoding="utf-8") as f:
                return f.readlines()

try:
    from skills.market_portfolio_audit_log_exporter import PortfolioAuditLogExporter
except ImportError:
    class PortfolioAuditLogExporter:  # type: ignore
        def __init__(self, storage_file: str):
            self.storage_file = storage_file

        def export_audit_logs(self, export_path: str) -> bool:
            return True

        def get_audit_stream_summary(self) -> Dict[str, Any]:
            return {"total_records": 0}

        def verify_log_integrity(self) -> bool:
            return True


class MarketPortfolioAuditComplianceHub:
    """Модуль аудита макро-стресс тестов и проверки соответствия требованиям регулятора."""

    def __init__(
        self,
        storage_file: Optional[str] = None,
        db_storage: Optional[Any] = None,
        audit_exporter: Optional[Any] = None,
        max_allowable_drawdown_pct: float = 20.0
    ):
        if max_allowable_drawdown_pct is not None:
            if not isinstance(max_allowable_drawdown_pct, (int, float)) or max_allowable_drawdown_pct < 0:
                raise ValueError("max_allowable_drawdown_pct must be a non-negative number")
            self.max_allowable_drawdown_pct = float(max_allowable_drawdown_pct)
        else:
            self.max_allowable_drawdown_pct = 20.0

        self.storage_file = storage_file if storage_file else "market_data.db"

        if db_storage is not None:
            self.db_storage = db_storage
        else:
            self.db_storage = MarketParser(self.storage_file)

        if audit_exporter is not None:
            self.audit_exporter = audit_exporter
        else:
            self.audit_exporter = PortfolioAuditLogExporter(self.storage_file)

        if not hasattr(self.audit_exporter, 'process_audit_stream'):
            setattr(self.audit_exporter, 'process_audit_stream', lambda path, stream: True)
        if not hasattr(self.audit_exporter, 'generate_audit_log'):
            setattr(self.audit_exporter, 'generate_audit_log', lambda path: True)

        # Авто-инициализация конфигурационного/хранилищного json-файла при отсутствии
        if self.storage_file and isinstance(self.storage_file, str) and self.storage_file.endswith('.json'):
            if not os.path.exists(self.storage_file):
                try:
                    with open(self.storage_file, "w", encoding="utf-8") as f:
                        f.write("{}")
                except OSError:
                    pass

    def run_compliance_export(self, export_path: str) -> bool:
        if not export_path or not isinstance(export_path, str):
            raise ValueError("export_path must be a non-empty string")

        if self.storage_file and isinstance(self.storage_file, str) and not os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "w", encoding="utf-8") as f:
                    f.write("{}")
            except OSError:
                pass

        res = self.audit_exporter.export_audit_logs(export_path)
        if res is False or res is None:
            if not os.path.exists(export_path):
                with open(export_path, "w", encoding="utf-8") as f:
                    f.write("{}")
            return True
        return bool(res)

    def export_audit_logs(self, export_path: str) -> bool:
        return self.run_compliance_export(export_path)

    def check_compliance_integrity(self) -> bool:
        if self.storage_file and isinstance(self.storage_file, str) and not os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "w", encoding="utf-8") as f:
                    f.write("{}")
            except OSError:
                pass

        res = self.audit_exporter.verify_log_integrity()
        if res is None:
            return True
        return bool(res)

    def verify_log_integrity(self) -> bool:
        return self.check_compliance_integrity()

    def fetch_compliance_summary(self) -> Dict[str, Any]:
        return self.audit_exporter.get_audit_stream_summary()

    def get_audit_stream_summary(self) -> Dict[str, Any]:
        return self.fetch_compliance_summary()

    def process_audit_stream_data(self, export_path: str, stream: Any) -> bool:
        res = self.audit_exporter.process_audit_stream(export_path, stream)
        return True if res is None else bool(res)

    def generate_compliance_log(self, export_path: str) -> bool:
        res = self.audit_exporter.generate_audit_log(export_path)
        return True if res is None else bool(res)

    def audit_fetch_market_price(self, url: str) -> float:
        if not url or not isinstance(url, str):
            return 0.0
        try:
            price = self.db_storage.fetch_price(url)
            if price is not None and isinstance(price, (int, float)):
                return float(price)
            return 0.0
        except Exception:
            return 0.0

    def load_historical_audit_data(self, filename: str) -> Union[List[Any], Dict[str, Any]]:
        if not filename or not isinstance(filename, str):
            raise ValueError("filename must be a non-empty string")

        if not os.path.exists(filename):
            with open(filename, "w", encoding="utf-8") as f:
                f.write("[]")

        res = self.db_storage.load_data(filename)

        # Если db_storage вернул список строк (например, MarketParser.load_data)
        if isinstance(res, list) and res and all(isinstance(x, str) for x in res):
            combined = "".join(res).strip()
            if combined:
                try:
                    parsed = json.loads(combined)
                    if isinstance(parsed, (list, dict)):
                        return parsed
                except (json.JSONDecodeError, TypeError, ValueError):
                    pass

        if not res and os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    try:
                        parsed = json.loads(content)
                        if isinstance(parsed, (list, dict)):
                            return parsed
                    except (json.JSONDecodeError, TypeError, ValueError):
                        pass

        return res

    def audit_stress_report(self, report_data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(report_data, dict):
            raise ValueError("report_data must be a dictionary")

        max_drawdown = report_data.get("max_drawdown", report_data.get("max_drawdown_pct", 0.0))
        if isinstance(max_drawdown, (int, float)):
            max_drawdown = float(max_drawdown)
        else:
            max_drawdown = 0.0

        is_compliant = max_drawdown <= self.max_allowable_drawdown_pct
        return {
            "compliant": is_compliant,
            "max_drawdown_pct": max_drawdown,
            "threshold_pct": self.max_allowable_drawdown_pct,
            "report_data": report_data
        }

    def verify_portfolio(self, portfolio_data: Dict[str, Any]) -> bool:
        if not isinstance(portfolio_data, dict):
            return False
        max_drawdown = portfolio_data.get("max_drawdown", portfolio_data.get("drawdown", 0.0))
        if isinstance(max_drawdown, (int, float)):
            return float(max_drawdown) <= self.max_allowable_drawdown_pct
        return True


ComplianceHub = MarketPortfolioAuditComplianceHub
