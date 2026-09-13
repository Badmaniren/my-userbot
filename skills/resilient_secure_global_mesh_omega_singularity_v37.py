from skills import (
    resilient_secure_global_mesh_omega_singularity_v36,
    resilient_secure_global_mesh_omega_transcendence_v32
)

class ResilientSecureGlobalMeshOmegaSingularityV37(
    resilient_secure_global_mesh_omega_singularity_v36.ResilientSecureGlobalMeshOmegaSingularityV36,
    resilient_secure_global_mesh_omega_transcendence_v32.ResilientSecureGlobalMeshOmegaTranscendenceV32
):
    def __init__(self, db_path=":memory:", max_memory_mb=512, calls=10, period=60, raise_on_limit=False):
        resilient_secure_global_mesh_omega_singularity_v36.ResilientSecureGlobalMeshOmegaSingularityV36.__init__(
            self, db_path=db_path, max_memory_mb=max_memory_mb, calls=calls, period=period, raise_on_limit=raise_on_limit
        )
        resilient_secure_global_mesh_omega_transcendence_v32.ResilientSecureGlobalMeshOmegaTranscendenceV32.__init__(
            self, db_path=db_path, max_memory_mb=max_memory_mb, calls=calls, period=period, raise_on_limit=raise_on_limit
        )

    def validate_target_headers(self, target, timeout=5):
        res_v36 = resilient_secure_global_mesh_omega_singularity_v36.ResilientSecureGlobalMeshOmegaSingularityV36.validate_target_headers(
            self, target, timeout
        )
        res_v32 = resilient_secure_global_mesh_omega_transcendence_v32.ResilientSecureGlobalMeshOmegaTranscendenceV32.validate_target_headers(
            self, target, timeout
        )
        return bool(res_v36 and res_v32)