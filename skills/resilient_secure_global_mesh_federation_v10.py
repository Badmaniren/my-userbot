from skills.resilient_secure_global_mesh_autonomous_matrix_v9 import ResilientSecureGlobalMeshAutonomousMatrixV9
from skills.resilient_secure_smart_crawler_hub_v11_global_mesh import ResilientSecureSmartCrawlerHubV11GlobalMesh


class ResilientSecureGlobalMeshFederationV10Error(Exception):
    """Custom exception for Resilient Secure Global Mesh Federation V10 errors."""
    pass


class ResilientSecureGlobalMeshFederationV10:
    def __init__(self, db_path=":memory:", max_memory_mb=512, calls=10, period=60, raise_on_limit=True):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit

        self.matrix_v9 = ResilientSecureGlobalMeshAutonomousMatrixV9(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )
        self.hub_v11 = ResilientSecureSmartCrawlerHubV11GlobalMesh(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )

    def validate_target_headers(self, target: str, timeout: int) -> bool:
        try:
            matrix_res = self.matrix_v9.validate_target_headers(target, timeout)
            hub_res = self.hub_v11.validate_target_headers(target, timeout)
            return bool(matrix_res and hub_res)
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureGlobalMeshFederationV10Error(str(e)) from e
            raise

    def coordinate_expansion(self, target: str, timeout: int) -> bool:
        try:
            matrix_res = self.matrix_v9.coordinate_expansion(target, timeout)
            hub_res = self.hub_v11.coordinate_expansion(target, timeout)
            return bool(matrix_res and hub_res)
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureGlobalMeshFederationV10Error(str(e)) from e
            raise

    def coordinate_expansion_safe(self, target: str, timeout: int) -> bool:
        try:
            matrix_res = self.matrix_v9.coordinate_expansion_safe(target, timeout)
            hub_res = self.hub_v11.coordinate_expansion_safe(target, timeout)
            return bool(matrix_res and hub_res)
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureGlobalMeshFederationV10Error(str(e)) from e
            raise

    def export_analytics_report(self, target: str, report_data: dict) -> None:
        try:
            self.matrix_v9.export_analytics_report(target, report_data)
            self.hub_v11.export_analytics_report(target, report_data)
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureGlobalMeshFederationV10Error(str(e)) from e
            raise

    def get_exported_report(self, target: str) -> dict:
        try:
            matrix_report = self.matrix_v9.get_exported_report(target) or {}
            hub_report = self.hub_v11.get_exported_report(target) or {}
            return {**matrix_report, **hub_report}
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureGlobalMeshFederationV10Error(str(e)) from e
            raise

    def process_stream(self, target: str, timeout: int):
        try:
            self.hub_v11.process_stream(target, timeout)
            return self.matrix_v9.process_stream(target, timeout)
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureGlobalMeshFederationV10Error(str(e)) from e
            raise

    def route_request(self, target: str, timeout: int):
        try:
            self.hub_v11.route_request(target, timeout) if hasattr(self.hub_v11, "route_request") else None
            return self.matrix_v9.route_request(target, timeout)
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureGlobalMeshFederationV10Error(str(e)) from e
            raise