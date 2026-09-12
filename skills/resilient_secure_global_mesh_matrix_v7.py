import requests
from typing import Dict, Any, Optional

from skills.resilient_secure_global_mesh_orchestrator_v6 import (
    ResilientSecureGlobalMeshOrchestratorV6
)
from skills.resilient_secure_global_mesh_coordinator_v5 import (
    ResilientSecureGlobalMeshCoordinatorV5
)


class ResilientSecureGlobalMeshMatrixV7Error(Exception):
    """Базовое исключение для ошибок матрицы v7."""
    pass


class ResilientSecureGlobalMeshMatrixV7(
    ResilientSecureGlobalMeshOrchestratorV6, 
    ResilientSecureGlobalMeshCoordinatorV5
):
    """Узел матричной меш-сети v7 (композиция v6 оркестратора и v5 координатора)."""

    def __init__(
        self,
        db_path: str = ":memory:",
        max_memory_mb: int = 512,
        calls: int = 10,
        period: float = 1.0,
        raise_on_limit: bool = True
    ):
        # Инициализируем базовые классы для обеспечения полной композиции
        ResilientSecureGlobalMeshOrchestratorV6.__init__(
            self,
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )
        ResilientSecureGlobalMeshCoordinatorV5.__init__(self)
        
        self.reports: Dict[str, Dict[str, Any]] = {}
        self.orchestrator = self

    def validate_target_headers(self, target: str, timeout: int = 5) -> bool:
        """Проверка заголовков целевого узла."""
        try:
            response = requests.head(target, timeout=timeout)
            return response.status_code == 200
        except Exception:
            return False

    def coordinate_expansion(self, target: str, timeout: int = 5) -> bool:
        """Координация расширения меш-сети."""
        return self.validate_target_headers(target, timeout)

    def coordinate_expansion_safe(self, target: str, timeout: int = 5) -> bool:
        """Безопасная координация расширения с перехватом исключений."""
        try:
            return self.validate_target_headers(target, timeout)
        except Exception:
            return False

    def export_analytics_report(self, target: str, report_data: Dict[str, Any]) -> None:
        """Экспорт аналитического отчета."""
        self.reports[target] = dict(report_data)

    def get_exported_report(self, target: str) -> Optional[Dict[str, Any]]:
        """Получение экспортированного отчета."""
        return self.reports.get(target)

    def process_stream(self, target: str, timeout: int = 5) -> Any:
        """Обработка потока данных с целевого узла."""
        response = requests.get(target, timeout=timeout, stream=True)
        if response.status_code != 200:
            raise ResilientSecureGlobalMeshMatrixV7Error(f"Stream failed with status {response.status_code}")
        return response.raw

    def route_request(self, target: str, timeout: int = 5) -> Any:
        """Маршрутизация запроса через меш-сеть."""
        response = requests.get(target, timeout=timeout)
        return response.text