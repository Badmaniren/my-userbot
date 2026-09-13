from skills.resilient_secure_global_mesh_omega_hive_v15 import ResilientSecureGlobalMeshOmegaHiveV15
from skills.resilient_secure_global_mesh_supreme_swarm_v14 import ResilientSecureGlobalMeshSupremeSwarmV14


class ResilientSecureGlobalMeshAbsoluteInterfaceV17Error(Exception):
    pass


class ResilientSecureGlobalMeshAbsoluteInterfaceV17(ResilientSecureGlobalMeshOmegaHiveV15):
    """
    Абсолютный Меш-Интерфейс v17: модуль объединяет Омега-Улей v15 и Высший Рой v14
    для создания единого конечного интерфейса управления меш-сетью.
    """

    def __init__(self, db_path=":memory:", max_memory_mb=512, calls=10, period=60, raise_on_limit=True):
        super().__init__(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )
        self.supreme_swarm = ResilientSecureGlobalMeshSupremeSwarmV14(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )
        self._exported_reports = {}

    def validate_target_headers(self, url, timeout=5):
        try:
            res = self.supreme_swarm.validate_target_headers(url, timeout=timeout)
            if isinstance(res, bool):
                return res
            return bool(res)
        except Exception as e:
            raise ResilientSecureGlobalMeshAbsoluteInterfaceV17Error(f"Validation failed: {e}") from e

    def coordinate_expansion(self, url, timeout=5):
        return self.supreme_swarm.coordinate_expansion(url, timeout=timeout)

    def coordinate_expansion_safe(self, url, timeout=5):
        try:
            res = self.supreme_swarm.coordinate_expansion(url, timeout=timeout)
            if isinstance(res, bool):
                return res
            return True
        except Exception:
            return False

    def export_analytics_report(self, target, report_data):
        self._exported_reports[target] = report_data
        if hasattr(self.supreme_swarm, "export_analytics_report"):
            self.supreme_swarm.export_analytics_report(target, report_data)

    def get_exported_report(self, target):
        if target in self._exported_reports:
            return self._exported_reports[target]
        if hasattr(self.supreme_swarm, "get_exported_report"):
            return self.supreme_swarm.get_exported_report(target)
        return {}

    def process_stream(self, url, timeout=5):
        if hasattr(self.supreme_swarm, "process_stream"):
            return self.supreme_swarm.process_stream(url, timeout=timeout)
        return super().process_stream(url, timeout=timeout)

    def route_request(self, url, timeout=5):
        if hasattr(self.supreme_swarm, "route_request"):
            return self.supreme_swarm.route_request(url, timeout=timeout)
        return super().route_request(url, timeout=timeout)