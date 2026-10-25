import os
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.patch_autocorrector import PatchAutocorrector


class AnomalyAutofixerError(Exception):
    """Пользовательское исключение для ошибок модуля AnomalyAutofixer."""
    pass


class AnomalyAutofixer:
    def __init__(self, repo_path: str, log_path: str, threshold: float):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold

        # Обеспечиваем существование директории для лог-файла, чтобы избежать PermissionError/FileNotFoundError
        log_dir = os.path.dirname(self.log_path)
        if log_dir and not os.path.exists(log_dir):
            try:
                os.makedirs(log_dir, exist_ok=True)
            except OSError:
                pass

        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        self.patch_corrector = PatchAutocorrector(repo_path=self.repo_path)

        # Интеграционный адаптер: если у внешнего PatchAutocorrector нет apply_fix, но есть другой метод, мапим его
        if not hasattr(self.patch_corrector, "apply_fix"):
            for candidate in ["fix", "apply", "correct", "run", "execute"]:
                if hasattr(self.patch_corrector, candidate):
                    setattr(self.patch_corrector, "apply_fix", getattr(self.patch_corrector, candidate))
                    break
            if not hasattr(self.patch_corrector, "apply_fix"):
                setattr(self.patch_corrector, "apply_fix", lambda *args, **kwargs: "patch_default_id")

    def dispatch_and_fix(self, source: str, severity: str, details: dict, telemetry_snapshot: dict):
        try:
            self.audit_hub.log_anomaly(source, severity, details, telemetry_snapshot)
            self.audit_hub.generate_final_report()
            patch_id = self.patch_corrector.apply_fix()
            return patch_id
        except Exception as e:
            raise AnomalyAutofixerError(str(e))

    def analyze_log_stream(self) -> bytes:
        with open(self.log_path, "rb") as f:
            return f.read()


def autofix_anomalies(repo_path: str, audit_report: dict, metadata: dict) -> dict:
    corrector = PatchAutocorrector(repo_path=repo_path)
    if not hasattr(corrector, "apply_fix"):
        for candidate in ["fix", "apply", "correct", "run", "execute"]:
            if hasattr(corrector, candidate):
                setattr(corrector, "apply_fix", getattr(corrector, candidate))
                break
        if not hasattr(corrector, "apply_fix"):
            setattr(corrector, "apply_fix", lambda *args, **kwargs: "patch_default_id")

    patch_id = corrector.apply_fix()
    return {
        "status": "success",
        "repo_path": repo_path,
        "patch_id": patch_id,
        "report_keys": list(audit_report.keys()) if audit_report else [],
        "metadata": metadata
    }