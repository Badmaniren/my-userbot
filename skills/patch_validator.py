import os
from skills.code_sanitizer import CodeSanitizer
from skills.system_telemetry import SystemTelemetry
from skills.patch_checker import PatchChecker
from skills.anomaly_audit_hub import AnomalyAuditHub

class PatchValidatorError(Exception):
    """Базовое исключение для ошибок валидации патчей."""
    pass

class PatchValidator:
    def __init__(self, sanitizer=None, audit_hub=None):
        self._sanitizer = sanitizer
        self._audit_hub = audit_hub

    @property
    def sanitizer(self):
        return self._sanitizer if self._sanitizer is not None else CodeSanitizer()

    @property
    def audit_hub(self):
        return self._audit_hub if self._audit_hub is not None else AnomalyAuditHub()

    def validate_structure(self, data: dict) -> bool:
        """Проверка наличия обязательных полей в структуре патча."""
        required_keys = {"id", "payload", "checksum"}
        if not all(key in data for key in required_keys):
            raise PatchValidatorError("Invalid patch structure")
        return True

    def verify_safety(self, content: str) -> bool:
        """Проверка безопасности кода через CodeSanitizer."""
        is_safe = self.sanitizer.is_safe(content)
        if not is_safe:
            self.audit_hub.log_anomaly("patch_validator", "CRITICAL", f"Unsafe content detected: {content[:20]}")
        return is_safe

    def check_integrity(self, path: str, telemetry=None) -> bool:
        """Проверка целостности файла с логированием в телеметрию."""
        if telemetry:
            telemetry.log_event(path)
        return os.path.exists(path)

    def full_validate(self, path: str) -> bool:
        """Сквозная валидация файла патча."""
        try:
            with open(path, 'r') as f:
                content = f.read()
        except (IOError, OSError) as e:
            raise PatchValidatorError(f"Failed to read patch file: {e}")

        checker = PatchChecker()
        return checker.check(content)

    def validate(self, data: dict) -> bool:
        """Интеграционный метод валидации данных."""
        if "id" not in data:
            return False

        content = data.get("payload") or data.get("content")
        if content and isinstance(content, str):
            if not self.verify_safety(content):
                raise PatchValidatorError("Unsafe patch content")

        return True