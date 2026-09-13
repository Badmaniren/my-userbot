from skills.resilient_secure_global_mesh_omega_singularity_v39 import ResilientSecureGlobalMeshOmegaSingularityV39
from skills.resilient_secure_global_mesh_omega_transcendence_v32 import ResilientSecureGlobalMeshOmegaTranscendenceV32

class ResilientSecureGlobalMeshOmegaSingularityV40:
    def __init__(self, db_path, max_mb, calls, period, raise_on_limit=True):
        self.v39_node = ResilientSecureGlobalMeshOmegaSingularityV39(
            db_path, max_mb, calls, period, raise_on_limit
        )
        self.v32_node = ResilientSecureGlobalMeshOmegaTranscendenceV32(
            db_path, max_mb, calls, period, raise_on_limit
        )

    def validate_target_headers(self, target, timeout):
        return bool(self.v39_node.validate_target_headers(target, timeout))

    def coordinate_expansion_safe(self, target, timeout):
        return bool(self.v39_node.coordinate_expansion_safe(target, timeout))

    def route_request(self, target, timeout):
        return self.v32_node.route_request(target, timeout)

    def process_stream(self, target, timeout):
        return self.v39_node.process_stream(target, timeout)

    def export_analytics_report(self, target, report_data):
        # Синхронизация данных в оба узла для обеспечения консистентности
        self.v39_node.export_analytics_report(target, report_data)
        self.v32_node.export_analytics_report(target, report_data)

    def get_exported_report(self, target):
        # Приоритет v32 как основного источника, fallback на v39
        report = self.v32_node.get_exported_report(target)
        if report is None:
            report = self.v39_node.get_exported_report(target)
        return report

    def coordinate_expansion(self, target, timeout):
        return bool(self.v39_node.coordinate_expansion(target, timeout))