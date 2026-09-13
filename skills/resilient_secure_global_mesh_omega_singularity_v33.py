from skills.resilient_secure_global_mesh_omega_transcendence_v32 import ResilientSecureGlobalMeshOmegaTranscendenceV32
from skills.resilient_secure_global_mesh_omega_singularity_v30 import ResilientSecureGlobalMeshOmegaSingularityV30
import skills.memory_profiler as memory_profiler

class ResilientSecureGlobalMeshOmegaSingularityV33:
    def __init__(self, db_path, max_memory_mb, calls, period, raise_on_limit):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.raise_on_limit = raise_on_limit
        self.transcendence_v32 = ResilientSecureGlobalMeshOmegaTranscendenceV32(db_path, calls, period)
        self.singularity_v30 = ResilientSecureGlobalMeshOmegaSingularityV30(db_path)

    def _enforce_memory(self):
        memory_profiler.assert_memory_limit(self.max_memory_mb)

    def validate_target_headers(self, target, timeout):
        self._enforce_memory()
        try:
            res = self.transcendence_v32.validate_target_headers(target, timeout)
            return bool(res)
        except Exception:
            if self.raise_on_limit:
                raise
            return False

    def coordinate_expansion(self, target, timeout):
        self._enforce_memory()
        return bool(self.singularity_v30.coordinate_expansion(target, timeout))

    def coordinate_expansion_safe(self, target, timeout):
        self._enforce_memory()
        return bool(self.singularity_v30.coordinate_expansion_safe(target, timeout))

    def route_request(self, target, timeout):
        self._enforce_memory()
        return self.transcendence_v32.route_request(target, timeout)

    def process_stream(self, target, timeout):
        self._enforce_memory()
        return self.singularity_v30.process_stream(target, timeout)

    def export_analytics_report(self, target, report_data):
        self._enforce_memory()
        self.transcendence_v32.export_analytics_report(target, report_data)
        return self.singularity_v30.export_analytics_report(target, report_data)

    def get_exported_report(self, target):
        self._enforce_memory()
        report = self.singularity_v30.get_exported_report(target)
        if report is not None:
            return report
        return self.transcendence_v32.get_exported_report(target)