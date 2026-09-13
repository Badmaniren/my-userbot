class ResilientSecureGlobalMeshOmegaTranscendenceV20Error(Exception):
    """Кастомное исключение для модуля Трансцендентности Омега v20."""
    pass


# Совместимость с опечаткой в интеграционном тесте (omega с маленькой w)
ResilientSecureGlobalMeshomegaTranscendenceV20Error = ResilientSecureGlobalMeshOmegaTranscendenceV20Error


class ResilientSecureGlobalMeshOmegaTranscendenceV20:
    def __init__(self, db_path=":memory:", max_memory_mb=512, calls=10, period=1.0, raise_on_limit=True):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit

        self._singularity_v45 = None
        self._transcendence_v32 = None
        self._reports = {}

    @property
    def singularity_v45(self):
        if self._singularity_v45 is None:
            from skills.resilient_secure_global_mesh_omega_singularity_v45 import (
                ResilientSecureGlobalMeshOmegaSingularityV45
            )
            self._singularity_v45 = ResilientSecureGlobalMeshOmegaSingularityV45(
                db_path=self.db_path,
                max_memory_mb=self.max_memory_mb,
                calls=self.calls,
                period=self.period,
                raise_on_limit=self.raise_on_limit
            )
        return self._singularity_v45

    @singularity_v45.setter
    def singularity_v45(self, value):
        self._singularity_v45 = value

    @property
    def transcendence_v32(self):
        if self._transcendence_v32 is None:
            from skills.resilient_secure_global_mesh_omega_transcendence_v32 import (
                ResilientSecureGlobalMeshOmegaTranscendenceV32
            )
            self._transcendence_v32 = ResilientSecureGlobalMeshOmegaTranscendenceV32(
                db_path=self.db_path,
                max_memory_mb=self.max_memory_mb,
                calls=self.calls,
                period=self.period,
                raise_on_limit=self.raise_on_limit
            )
        return self._transcendence_v32

    @transcendence_v32.setter
    def transcendence_v32(self, value):
        self._transcendence_v32 = value

    def validate_target_headers(self, target: str, timeout: int = 5) -> bool:
        try:
            res1 = self.singularity_v45.validate_target_headers(target, timeout=timeout)
            res2 = self.transcendence_v32.validate_target_headers(target, timeout=timeout)
            return bool(res1 and res2)
        except Exception as e:
            if isinstance(e, ResilientSecureGlobalMeshOmegaTranscendenceV20Error):
                raise
            return False

    def coordinate_expansion(self, target: str, timeout: int = 5) -> bool:
        try:
            res1 = self.singularity_v45.coordinate_expansion(target, timeout=timeout)
            res2 = self.transcendence_v32.coordinate_expansion(target, timeout=timeout)
            return bool(res1 and res2)
        except Exception as e:
            if isinstance(e, ResilientSecureGlobalMeshOmegaTranscendenceV20Error):
                raise
            return False

    def coordinate_expansion_safe(self, target: str, timeout: int = 5) -> bool:
        try:
            res1 = self.singularity_v45.coordinate_expansion_safe(target, timeout=timeout)
            res2 = self.transcendence_v32.coordinate_expansion_safe(target, timeout=timeout)
            return bool(res1 and res2)
        except Exception as e:
            if isinstance(e, ResilientSecureGlobalMeshOmegaTranscendenceV20Error):
                raise
            return False

    def route_request(self, target: str, timeout: int = 5) -> str:
        try:
            return self.singularity_v45.route_request(target, timeout=timeout)
        except Exception:
            return self.transcendence_v32.route_request(target, timeout=timeout)

    def process_stream(self, target: str, timeout: int = 5) -> None:
        self.singularity_v45.process_stream(target, timeout=timeout)
        self.transcendence_v32.process_stream(target, timeout=timeout)

    def export_analytics_report(self, target: str, report_data: dict) -> None:
        self._reports[target] = {**report_data}
        self.singularity_v45.export_analytics_report(target, report_data)
        self.transcendence_v32.export_analytics_report(target, report_data)

    def get_exported_report(self, target: str) -> dict:
        report = self._reports.get(target, {})
        return {**report}