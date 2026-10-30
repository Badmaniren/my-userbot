import io
from skills import patch_sanitizer, patch_checker, patch_applier
from skills.patch_sanitizer import PatchSanitizerError
from skills.patch_checker import PatchCheckerError
from skills.patch_applier import PatchApplierError

class PatchPipelineError(Exception):
    """Исключение, возникающее при ошибках в пайплайне патчей."""
    pass

class PatchPipeline:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path

    def process_patch(self, stream: io.BytesIO, target_file: str, policy: str) -> bool:
        try:
            # Чтение данных из потока
            raw_data = stream.read()
            if isinstance(raw_data, bytes):
                raw_patch = raw_data.decode('utf-8', errors='ignore')
            else:
                raw_patch = raw_data

            # 1. Санитизация
            sanitized_output = patch_sanitizer.sanitize_patch(raw_patch)

            # 2. Проверка
            check_result = patch_checker.check_patch(sanitized_output, self.repo_path, target_file, policy)

            # Проверка статуса отчета проверки
            if isinstance(check_result, dict):
                status = check_result.get("status")
                if status and status != "passed":
                    errors = check_result.get("errors", ["Patch check failed"])
                    raise PatchPipelineError(f"Policy violation: {errors[0] if errors else 'Unknown error'}")

            # 3. Применение
            success = patch_applier.apply_patch(self.repo_path, sanitized_output)
            if not success:
                raise PatchPipelineError("Patch applier returned False")

            return True

        except (PatchSanitizerError, PatchCheckerError, PatchApplierError, PatchPipelineError) as e:
            raise PatchPipelineError(str(e)) from e
        except Exception as e:
            raise PatchPipelineError(f"Unexpected pipeline error: {e}") from e

def run_pipeline(raw_patch, repo_path: str, target_file: str, policy: str = "strict") -> bool:
    """Интеграционная функция для запуска конвейера из строки или потока."""
    if isinstance(raw_patch, str):
        stream = io.BytesIO(raw_patch.encode('utf-8'))
    elif isinstance(raw_patch, bytes):
        stream = io.BytesIO(raw_patch)
    elif hasattr(raw_patch, "read"):
        stream = raw_patch
    else:
        # Для обработки некорректных типов данных (например, None), вызывающих ошибку в санитизаторе
        stream = io.BytesIO(str(raw_patch).encode('utf-8'))

    pipeline = PatchPipeline(repo_path=repo_path)
    return pipeline.process_patch(stream, target_file, policy)