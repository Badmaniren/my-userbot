import requests
from skills.resilient_secure_global_mesh_synthetic_intelligence_v16 import (
    ResilientSecureGlobalMeshSyntheticIntelligenceV16
)
from skills.resilient_secure_global_mesh_omega_hive_v15 import (
    ResilientSecureGlobalMeshOmegaHiveV15
)


class ResilientSecureGlobalMeshInterfaceV17Error(Exception):
    """Кастомное исключение для интерфейса меш-сети v17."""
    pass


class ResilientSecureGlobalMeshInterfaceV17:
    def __init__(
        self,
        db_path: str = ":memory:",
        max_memory_mb: int = 512,
        calls: int = 10,
        period: float = 1.0,
        raise_on_limit: bool = True
    ):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit

        self.synthetic_intelligence = ResilientSecureGlobalMeshSyntheticIntelligenceV16(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )
        self.omega_hive = ResilientSecureGlobalMeshOmegaHiveV15(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )

    def validate_target_headers(self, target: str, timeout: float = 5) -> bool:
        try:
            response = requests.head(target, timeout=timeout)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def coordinate_expansion(self, target: str, timeout: float = 5) -> bool:
        si_res = self.synthetic_intelligence.coordinate_expansion(target, timeout)
        oh_res = self.omega_hive.coordinate_expansion(target, timeout)
        return bool(si_res and oh_res)

    def coordinate_expansion_safe(self, target: str, timeout: float = 5) -> bool:
        si_res = self.synthetic_intelligence.coordinate_expansion_safe(target, timeout)
        oh_res = self.omega_hive.coordinate_expansion_safe(target, timeout)
        return bool(si_res and oh_res)

    def export_analytics_report(self, target: str, report_data: dict) -> None:
        self.synthetic_intelligence.export_analytics_report(target, report_data)
        self.omega_hive.export_analytics_report(target, report_data)

    def get_exported_report(self, target: str) -> dict:
        return self.synthetic_intelligence.get_exported_report(target)

    def process_stream(self, target: str, timeout: float = 5) -> None:
        self.synthetic_intelligence.process_stream(target, timeout)
        self.omega_hive.process_stream(target, timeout)

    def route_request(self, target: str, timeout: float = 5):
        return self.synthetic_intelligence.route_request(target, timeout=timeout)
