from skills.patch_analyzer import PatchAnalyzer
from skills.patch_applier import PatchApplier
from skills.patch_checker import PatchChecker
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.git_inspector import GitInspector
from skills.patch_sanitizer import PatchSanitizer


class PatchRunnerError(Exception):
    """Исключение, возникающее в процессе работы PatchRunner."""
    pass


class PatchRunner:
    def __init__(self, repo_path: str, log_path: str = "/tmp/anomaly.log", threshold: float = 0.5):
        self.repo_path = repo_path
        self.log_path = log_path
        self.threshold = threshold
        self.analyzer = PatchAnalyzer()
        self.applier = PatchApplier(repo_path=self.repo_path)
        self.checker = PatchChecker(repo_path=self.repo_path)
        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        self.git_inspector = GitInspector(repo_path=self.repo_path)
        self.sanitizer = PatchSanitizer()

    def run_pipeline(self, patch_data: str) -> bool:
        try:
            analysis_result = self.analyzer.analyze(patch_data)

            actual_patch_source = patch_data
            temp_file_path = None

            if "\n" in patch_data or patch_data.startswith("diff --git"):
                import tempfile
                tf = tempfile.NamedTemporaryFile(mode="w", delete=False)
                tf.write(patch_data)
                tf.close()
                temp_file_path = tf.name
                actual_patch_source = temp_file_path

            try:
                apply_success = self.applier.apply_patch(actual_patch_source)
            finally:
                if temp_file_path and __import__("os").path.exists(temp_file_path):
                    __import__("os").remove(temp_file_path)

            check_result = self.checker.check(patch_data)

            try:
                snapshot = analysis_result if isinstance(analysis_result, dict) else {"result": analysis_result}
                self.audit_hub.log_anomaly(
                    source="PatchRunner",
                    severity="INFO",
                    details={"status": "Pipeline executed"},
                    telemetry_snapshot=snapshot
                )
            except Exception as audit_error:
                raise PatchRunnerError(f"Audit hub logging failed: {audit_error}") from audit_error

            if isinstance(check_result, dict):
                check_ok = check_result.get("is_safe", True) and check_result.get("is_valid", True)
            else:
                check_ok = bool(check_result)

            return bool(apply_success and check_ok)
        except Exception as e:
            if not isinstance(e, PatchRunnerError):
                raise PatchRunnerError(str(e)) from e
            raise

    def fetch_latest_repo_changes(self):
        return self.git_inspector.get_latest_changes()

    def sanitize_incoming_patch(self, patch_data: str) -> str:
        return self.sanitizer.sanitize(patch_data)


def patch_runner_pipeline(repo_path: str, log_path: str = None, target_id: str = None, patch_data: str = ""):
    log_p = log_path if log_path else "/tmp/anomaly.log"
    runner = PatchRunner(repo_path=repo_path, log_path=log_p)
    if patch_data:
        return runner.run_pipeline(patch_data)
    return True
