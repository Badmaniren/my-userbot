from skills.patch_sanitizer import PatchSanitizer
from skills.patch_verifier import PatchVerifier
from skills.patch_applier import PatchApplier

class PatchRunner:
    """
    Класс для управления процессом применения патчей:
    санитизация, верификация и безопасное применение.
    """
    def __init__(self, repo_path):
        self.repo_path = repo_path
        self.sanitizer = PatchSanitizer()
        self.verifier = PatchVerifier(repo_path)
        self.applier = PatchApplier(repo_path)

    def run_pipeline(self, raw_patch):
        """
        Сквозной запуск пайплайна патчей.
        """
        # 1. Санитизация
        sanitized_patch = self.sanitizer.sanitize(raw_patch)

        # 2. Верификация
        if not self.verifier.verify(sanitized_patch):
            return False

        # 3. Применение
        return self.applier.safe_apply(sanitized_patch)

def run_patch_pipeline(repo_path, sanitized_patch):
    """
    Функция-обертка для интеграционного теста,
    использующая PatchRunner для сквозного процесса.
    """
    runner = PatchRunner(repo_path)
    try:
        return runner.run_pipeline(sanitized_patch)
    except Exception:
        return False