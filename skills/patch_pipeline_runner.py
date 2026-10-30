from skills.patch_sanitizer import PatchSanitizer, PatchSanitizerError
from skills.patch_checker import PatchChecker, PatchCheckerError
from skills.patch_applier import PatchApplier, PatchApplierError


class PatchPipelineRunner:
    """
    Интеграционный модуль для последовательного запуска этапов санитизации,
    проверки и применения патчей.
    """

    def __init__(self, repo_path):
        self.repo_path = repo_path

    @property
    def sanitizer(self):
        if not hasattr(self, '_sanitizer') or self._sanitizer is None:
            return PatchSanitizer()
        return self._sanitizer

    @sanitizer.setter
    def sanitizer(self, value):
        self._sanitizer = value

    @property
    def checker(self):
        if not hasattr(self, '_checker') or self._checker is None:
            return PatchChecker(repo_path=self.repo_path)
        return self._checker

    @checker.setter
    def checker(self, value):
        self._checker = value

    @property
    def applier(self):
        if not hasattr(self, '_applier') or self._applier is None:
            return PatchApplier(repo_path=self.repo_path)
        return self._applier

    @applier.setter
    def applier(self, value):
        self._applier = value

    def run(self, raw_patch, backup_tag=None):
        """
        Основной метод запуска пайплайна.
        """
        sanitized_patch = self.sanitizer.sanitize(raw_patch)
        self.checker.check_patch(sanitized_patch)

        if backup_tag:
            self.applier.create_recovery_point(backup_tag)
        try:
            return self.applier.apply_patch(sanitized_patch)
        except PatchApplierError:
            if backup_tag:
                self.applier.rollback(backup_tag)
            else:
                self.applier.rollback()
            raise

    def run_from_stream(self, stream):
        """
        Обработка патча из потока данных.
        """
        sanitized_patch = self.sanitizer.sanitize(stream)
        self.checker.check_patch(sanitized_patch)
        return self.applier.apply_patch(sanitized_patch)

    def run_pipeline(self, raw_patch, backup_tag=None):
        """
        Метод для интеграционных тестов с поддержкой backup_tag.
        """
        try:
            return self.run(raw_patch, backup_tag=backup_tag)
        except (PatchSanitizerError, PatchCheckerError, PatchApplierError):
            return False
        except Exception:
            return False