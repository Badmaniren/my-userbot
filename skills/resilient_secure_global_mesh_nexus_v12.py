import logging
from skills.resilient_secure_global_mesh_gateway_v11 import ResilientSecureGlobalMeshGatewayV11
from skills.resilient_secure_smart_crawler_hub_v11_global_mesh import ResilientSecureSmartCrawlerHubV11GlobalMesh

logger = logging.getLogger(__name__)


class ResilientSecureGlobalMeshNexusV12Error(Exception):
    """Кастомное исключение для ResilientSecureGlobalMeshNexusV12."""
    pass


class ResilientSecureGlobalMeshNexusV12:
    """Центральный меш-нексус v12, созданный путем композиции шлюза v11 и хаба v11."""

    def __init__(self, db_path=":memory:", max_memory_mb=512, calls=10, period=1.0, raise_on_limit=False):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit

        # Композиция: инициализация шлюза и хаба
        self.gateway = ResilientSecureGlobalMeshGatewayV11(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )
        self.hub = ResilientSecureSmartCrawlerHubV11GlobalMesh(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

    def validate_target_headers(self, target: str, timeout: int = 5) -> bool:
        """Валидация заголовков через компоненты шлюза и хаба."""
        try:
            gw_res = bool(self.gateway.validate_target_headers(target, timeout))
            hub_res = bool(self.hub.validate_target_headers(target, timeout))
            return gw_res and hub_res
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureGlobalMeshNexusV12Error(str(e)) from e
            return False

    def coordinate_expansion(self, target: str, timeout: int = 5) -> bool:
        """Координация расширения сети."""
        try:
            gw_res = bool(self.gateway.coordinate_expansion(target, timeout))
            hub_res = bool(self.hub.coordinate_expansion(target, timeout))
            return gw_res and hub_res
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureGlobalMeshNexusV12Error(str(e)) from e
            return False

    def coordinate_expansion_safe(self, target: str, timeout: int = 5) -> bool:
        """Безопасная координация расширения сети с перехватом исключений."""
        try:
            gw_res = bool(self.gateway.coordinate_expansion_safe(target, timeout))
            hub_res = bool(self.hub.coordinate_expansion_safe(target, timeout))
            return gw_res and hub_res
        except Exception:
            return False

    def export_analytics_report(self, target: str, report_data: dict) -> None:
        """Экспорт аналитического отчета."""
        self.gateway.export_analytics_report(target, report_data)
        self.hub.export_analytics_report(target, report_data)

    def get_exported_report(self, target: str) -> dict:
        """Получение экспортированного отчета."""
        return self.gateway.get_exported_report(target)

    def process_stream(self, target: str, timeout: int = 5):
        """Обработка потока данных."""
        try:
            return self.gateway.process_stream(target, timeout)
        except Exception as e:
            raise ResilientSecureGlobalMeshNexusV12Error(str(e)) from e

    def route_request(self, target: str, timeout: int = 5):
        """Маршрутизация запроса."""
        try:
            return self.gateway.route_request(target, timeout)
        except Exception as e:
            raise ResilientSecureGlobalMeshNexusV12Error(str(e)) from e