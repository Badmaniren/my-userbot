import os
import io

from skills.git_inspector import GitInspector
from skills.code_sanitizer import CodeSanitizer
from skills.patch_sanitizer import PatchSanitizer
from skills.patch_checker import PatchChecker
from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_alert_dispatcher import AnomalyAlertDispatcher


class PatchValidatorError(Exception):
    """Базовое исключение для ошибок валидации патчей."""
    pass


class PatchValidator:
    def __init__(self, repo_path=None, inspector=None, audit_hub=None, logger=None):
        self.repo_path = repo_path
        self.inspector = inspector
        self.audit_hub = audit_hub
        self.logger = logger
        self.max_patch_size = 1024 * 1024

    def _get_logger(self):
        return self.logger or AnomalyLogger()

    def _get_inspector(self):
        return self.inspector or GitInspector(repo_path=self.repo_path)

    def validate_integrity(self, patch_id):
        if patch_id is None:
            self._get_logger().log_anomaly("integrity failure: Invalid patch ID")
            raise PatchValidatorError("Invalid patch ID")

        if isinstance(patch_id, str) and len(patch_id) >= self.max_patch_size:
            raise PatchValidatorError("Patch size exceeds limit")

        inspector = self._get_inspector()
        diff = inspector.get_file_diff(patch_id)
        return bool(diff)

    def validate_security(self, content):
        sanitizer = CodeSanitizer()
        try:
            sanitizer.check(content)
        except Exception as e:
            raise PatchValidatorError(f"Security violation: {e}") from e

    def run_validation_pipeline(self, patch_data, patch_id):
        sanitizer = PatchSanitizer()
        checker = PatchChecker()

        sanitized_data = sanitizer.sanitize(patch_data)
        return checker.check(sanitized_data)

    def process_patch_file(self, file_path):
        with open(file_path, 'r') as f:
            content = f.read()
            if isinstance(content, bytes):
                return content.decode('utf-8', errors='ignore')
            return content

    def force_fail(self, patch_id):
        dispatcher = AnomalyAlertDispatcher()
        dispatcher.dispatch(patch_id)
        raise PatchValidatorError("Forced failure")

    def validate(self, patch_id, file_path, severity):
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        if "os.system" in content or "rm -rf" in content:
            self._get_logger().log_anomaly(f"Security anomaly detected in patch {patch_id}")
            return False

        if self.audit_hub:
            if hasattr(self.audit_hub, 'register_patch'):
                self.audit_hub.register_patch(patch_id, severity)

        self._get_logger().log_anomaly(f"Patch {patch_id} validated successfully")
        return True