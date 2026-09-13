from skills.resilient_secure_global_mesh_omega_genesis_v23 import (
    ResilientSecureGlobalMeshOmegaGenesisV23,
)
from skills.resilient_secure_global_mesh_omega_transcendence_v20 import (
    ResilientSecureGlobalMeshOmegaTranscendenceV20,
)


class ResilientSecureGlobalMeshOmegaNexusV24Error(Exception):
    """Кастомное исключение для модуля Nexus V24."""
    pass


class ResilientSecureGlobalMeshOmegaNexusV24(
    ResilientSecureGlobalMeshOmegaGenesisV23,
    ResilientSecureGlobalMeshOmegaTranscendenceV20
):
    def __init__(self, db_path=":memory:", max_memory_mb=512, calls=10, period=1.0, raise_on_limit=False):
        self._reports = {}
        try:
            super().__init__(
                db_path=db_path,
                max_memory_mb=max_memory_mb,
                calls=calls,
                period=period,
                raise_on_limit=raise_on_limit
            )
        except TypeError:
            try:
                ResilientSecureGlobalMeshOmegaGenesisV23.__init__(
                    self,
                    db_path=db_path,
                    max_memory_mb=max_memory_mb,
                    calls=calls,
                    period=period,
                    raise_on_limit=raise_on_limit
                )
            except TypeError:
                ResilientSecureGlobalMeshOmegaGenesisV23.__init__(self)

            try:
                ResilientSecureGlobalMeshOmegaTranscendenceV20.__init__(self)
            except TypeError:
                pass

    def validate_target_headers(self, target: str, timeout: int) -> bool:
        try:
            res = super().validate_target_headers(target, timeout)
            return bool(res)
        except (ValueError, RuntimeError, ConnectionError, TypeError):
            return False

    def coordinate_expansion(self, target: str, timeout: int) -> bool:
        try:
            res = super().coordinate_expansion(target, timeout)
            return bool(res)
        except (ValueError, RuntimeError, ConnectionError, TypeError):
            return False

    def coordinate_expansion_safe(self, target: str, timeout: int) -> bool:
        try:
            res = super().coordinate_expansion_safe(target, timeout)
            if not res:
                return False
            return bool(res)
        except (ValueError, RuntimeError, ConnectionError, TypeError):
            return False

    def route_request(self, target: str, timeout: int):
        try:
            res = super().route_request(target, timeout)
            if isinstance(res, Exception):
                raise res
            if res is None:
                raise ResilientSecureGlobalMeshOmegaNexusV24Error("Route request returned None")
            return res
        except (ResilientSecureGlobalMeshOmegaNexusV24Error, RuntimeError, ConnectionError, ValueError) as e:
            raise ResilientSecureGlobalMeshOmegaNexusV24Error(f"Route request failed: {e}") from e

    def process_stream(self, target: str, timeout: int):
        if hasattr(super(), "process_stream"):
            return super().process_stream(target, timeout)

    def export_analytics_report(self, target: str, report_data: dict) -> None:
        if hasattr(super(), "export_analytics_report"):
            try:
                super().export_analytics_report(target, report_data)
            except (ValueError, RuntimeError, TypeError):
                pass
        self._reports[target] = {**report_data}

    def get_exported_report(self, target: str) -> dict:
        if hasattr(super(), "get_exported_report"):
            try:
                res = super().get_exported_report(target)
                if res:
                    return res
            except (ValueError, RuntimeError, TypeError):
                pass
        return self._reports.get(target, {})
