import io
import skills.patch_sanitizer as patch_sanitizer
import skills.patch_checker as patch_checker
import skills.patch_applier as patch_applier

class PatchPipelineController:
    """
    Интеграционный узел для управления жизненным циклом патча:
    санитизация -> проверка -> применение.
    """

    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    @property
    def sanitizer(self):
        return patch_sanitizer.PatchSanitizer()

    @property
    def checker(self):
        return patch_checker.PatchChecker(repo_path=self.repo_path)

    @property
    def applier(self):
        return patch_applier.PatchApplier(repo_path=self.repo_path)

    def _is_check_valid(self, check_result: dict) -> bool:
        if not isinstance(check_result, dict):
            return False
        if "status" in check_result:
            return check_result.get("status") == "valid"
        return check_result.get("is_valid", True) and check_result.get("is_safe", True)

    def process(self, raw_patch: str, backup_tag: str = None) -> bool:
        """
        Основной поток обработки патча.
        """
        sanitized_patch = self.sanitizer.sanitize(raw_patch)

        check_result = self.checker.check_patch(sanitized_patch)
        if not self._is_check_valid(check_result):
            return False

        try:
            success = self.applier.apply_patch(sanitized_patch)
        except Exception:
            if backup_tag:
                self.applier.rollback(backup_tag)
            raise

        if not success and backup_tag:
            self.applier.rollback(backup_tag)

        return success

    def sanitize_stream(self, stream):
        """
        Прокси-метод для санитизации потока данных.
        """
        return self.sanitizer.sanitize(stream)

    def process_patch(self, patch_stream: str, target_file: str = None) -> bool:
        """
        Интеграционный метод для обработки патча с учетом целевого файла.
        """
        sanitized = self.sanitizer.sanitize(patch_stream)

        check_result = self.checker.check_patch(sanitized, target_file=target_file)
        if not self._is_check_valid(check_result):
            return False

        return self.applier.apply_patch(sanitized)

    def apply_with_backup(self, patch_stream: str, backup_tag: str) -> bool:
        """
        Применение патча с созданием точки восстановления.
        """
        if backup_tag:
            self.applier.create_recovery_point(backup_tag)

        sanitized = self.sanitizer.sanitize(patch_stream)

        check_result = self.checker.check_patch(sanitized)
        if not self._is_check_valid(check_result):
            return False

        try:
            return self.applier.apply_patch(sanitized)
        except Exception:
            if backup_tag:
                self.applier.rollback(backup_tag)
            raise