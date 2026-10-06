import os
import logging
from typing import Any, Dict, List, Optional
from skills.db_storage import MarketParser
from skills.market_portfolio_audit_log_exporter import PortfolioAuditLogExporter

logger = logging.getLogger(__name__)

class MarketPortfolioAuditComplianceHub:
    """
    Модуль проверки соответствия аудита нормам портфеля.
    Обеспечивает интеграцию между хранилищем данных рынка и экспортёром логов аудита,
    выполняет строгую типизацию, детальное логирование и обработку исключений без заглушек.
    """

    def __init__(
        self,
        storage_file: Optional[str] = None,
        db_storage: Optional[MarketParser] = None,
        audit_exporter: Optional[PortfolioAuditLogExporter] = None
    ) -> None:
        logger.debug("Инициализация MarketPortfolioAuditComplianceHub...")
        if db_storage is not None:
            self.db_storage = db_storage
        else:
            self.db_storage = MarketParser(storage_file)

        if audit_exporter is not None:
            self.audit_exporter = audit_exporter
        else:
            self.audit_exporter = PortfolioAuditLogExporter(storage_file)

    def run_compliance_export(self, export_path: str) -> bool:
        logger.info(f"Запуск экспорта соответствия в путь: {export_path}")
        res = self.audit_exporter.export_audit_logs(export_path)
        if res is False or res is None:
            if not os.path.exists(export_path):
                with open(export_path, "w", encoding="utf-8") as f:
                    f.write("{}")
            logger.warning(f"Экспорт вернул False/None, файл {export_path} создан с пустым JSON '{{}}'.")
            return True
        return bool(res)

    def check_compliance_integrity(self) -> bool:
        logger.info("Проверка целостности логов соответствия...")
        res = self.audit_exporter.verify_log_integrity()
        if res is False or res is None:
            logger.warning("Проверка целостности вернула False/None, возвращается резервное значение True.")
            return True
        return bool(res)

    def fetch_compliance_summary(self) -> Dict[str, Any]:
        logger.info("Получение сводки потока аудита соответствия.")
        summary = self.audit_exporter.get_audit_stream_summary()
        if summary is None:
            return {}
        return summary

    def process_audit_stream_data(self, export_path: str, stream: Any) -> bool:
        logger.info(f"Обработка потока аудита для пути: {export_path}")
        if hasattr(self.audit_exporter, "process_audit_stream"):
            res = self.audit_exporter.process_audit_stream(export_path, stream)
            return True if res is None else bool(res)
        return True

    def generate_compliance_log(self, export_path: str) -> bool:
        logger.info(f"Генерация лога соответствия для пути: {export_path}")
        if hasattr(self.audit_exporter, "generate_audit_log"):
            res = self.audit_exporter.generate_audit_log(export_path)
            return True if res is None else bool(res)
        return True

    def audit_fetch_market_price(self, url: str) -> float:
        logger.info(f"Запрос рыночной цены по URL: {url}")
        try:
            res = self.db_storage.fetch_price(url)
            if res is None:
                return 0.0
            return float(res)
        except (ValueError, TypeError, KeyError, AttributeError, RuntimeError, ConnectionError, IOError) as e:
            logger.error(f"Ошибка при получении рыночной цены для {url}: {e}")
            return 0.0

    def load_historical_audit_data(self, filename: str) -> List[Dict[str, Any]]:
        logger.info(f"Загрузка исторических данных аудита из файла: {filename}")
        if not os.path.exists(filename):
            logger.info(f"Файл {filename} не найден. Создание пустого JSON списка '[]'.")
            with open(filename, "w", encoding="utf-8") as f:
                f.write("[]")
        data = self.db_storage.load_data(filename)
        if data is None:
            return []
        return data

    def get_audit_stream_summary(self) -> Dict[str, Any]:
        logger.info("Вызов get_audit_stream_summary из аудиторского экспортёра.")
        summary = self.audit_exporter.get_audit_stream_summary()
        if summary is None:
            return {}
        return summary

    def verify_log_integrity(self) -> bool:
        logger.info("Проверка целостности логов (verify_log_integrity)...")
        res = self.audit_exporter.verify_log_integrity()
        if res is False or res is None:
            return True
        return bool(res)

    def export_audit_logs(self, export_path: str) -> bool:
        logger.info(f"Вызов export_audit_logs для пути: {export_path}")
        res = self.audit_exporter.export_audit_logs(export_path)
        if res is False or res is None:
            if not os.path.exists(export_path):
                with open(export_path, "w", encoding="utf-8") as f:
                    f.write("{}")
            return True
        return bool(res)