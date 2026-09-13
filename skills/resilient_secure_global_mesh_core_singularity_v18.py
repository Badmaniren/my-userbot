from skills.resilient_secure_global_mesh_interface_v17 import ResilientSecureGlobalMeshInterfaceV17
from skills.resilient_secure_global_mesh_synthetic_intelligence_v16 import ResilientSecureGlobalMeshSyntheticIntelligenceV16


class ResilientSecureGlobalMeshCoreSingularityV18Error(Exception):
    """Custom exception for ResilientSecureGlobalMeshCoreSingularityV18 errors."""
    pass


class ResilientSecureGlobalMeshCoreSingularityV18:
    def __init__(self, db_path=":memory:", max_memory_mb=512, calls=10, period=1.0, raise_on_limit=True):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit

        self.v17_interface = ResilientSecureGlobalMeshInterfaceV17(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )
        self.v16_ai = ResilientSecureGlobalMeshSyntheticIntelligenceV16(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

    def validate_target_headers(self, target, timeout):
        try:
            res_v17 = self.v17_interface.validate_target_headers(target, timeout)
            res_v16 = self.v16_ai.validate_target_headers(target, timeout)
            return bool(res_v17 and res_v16)
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureGlobalMeshCoreSingularityV18Error(str(e)) from e
            raise

    def coordinate_expansion(self, target, timeout):
        try:
            res_v17 = self.v17_interface.coordinate_expansion(target, timeout)
            res_v16 = self.v16_ai.coordinate_expansion(target, timeout)
            return bool(res_v17 and res_v16)
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureGlobalMeshCoreSingularityV18Error(str(e)) from e
            raise

    def coordinate_expansion_safe(self, target, timeout):
        try:
            res_v17 = self.v17_interface.coordinate_expansion_safe(target, timeout)
            return bool(res_v17)
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureGlobalMeshCoreSingularityV18Error(str(e)) from e
            raise

    def export_analytics_report(self, target, report_data):
        try:
            return self.v17_interface.export_analytics_report(target, report_data)
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureGlobalMeshCoreSingularityV18Error(str(e)) from e
            raise

    def get_exported_report(self, target):
        try:
            return self.v17_interface.get_exported_report(target)
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureGlobalMeshCoreSingularityV18Error(str(e)) from e
            raise

    def process_stream(self, target, timeout):
        try:
            res_v17 = self.v17_interface.process_stream(target, timeout)
            try:
                self.v16_ai.process_stream(target, timeout)
            except Exception as e:
                if self.raise_on_limit:
                    raise ResilientSecureGlobalMeshCoreSingularityV18Error(str(e)) from e
                raise
            return res_v17
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureGlobalMeshCoreSingularityV18Error(str(e)) from e
            raise

    def route_request(self, target, timeout):
        try:
            return self.v17_interface.route_request(target, timeout)
        except Exception as e:
            if self.raise_on_limit:
                raise ResilientSecureGlobalMeshCoreSingularityV18Error(str(e)) from e
            raise