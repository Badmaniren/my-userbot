import io
import os
import tempfile
from skills.patch_sanitizer import PatchSanitizer, PatchSanitizerError
from skills.patch_applier import PatchApplier, PatchApplierError


class PatchPipelineError(Exception):
    """Исключение, возникающее при ошибках в конвейере обработки патчей."""
    pass


def execute_patch_pipeline(repo_path, patch_source, backup_tag=None):
    """
    Связывает санитизацию патчей и их применение в единый рабочий конвейер.

    Принимает путь к репозиторию и источник патча (строка или поток ввода),
    санитизирует его, а затем применяет с помощью PatchApplier.
    """
    try:
        if patch_source is None:
            raise PatchSanitizerError("Patch source cannot be None.")
        sanitizer = PatchSanitizer()
        # Если patch_source передан как строка, оборачиваем в StringIO для совместимости со стримами
        if isinstance(patch_source, str):
            patch_source = io.StringIO(patch_source)
        sanitized_patch = sanitizer.sanitize(patch_source)
    except PatchSanitizerError as e:
        raise PatchPipelineError(f"Sanitization failed: {e}") from e
    except Exception as e:
        raise PatchPipelineError(f"Unexpected sanitization error: {e}") from e

    temp_patch_path = None
    try:
        applier = PatchApplier(repo_path=repo_path)
        if backup_tag:
            try:
                applier.create_recovery_point(backup_tag)
            except Exception as e:
                raise PatchPipelineError(f"Failed to create recovery point: {e}") from e

        target_dir = repo_path if repo_path and os.path.isdir(repo_path) else None
        # Записываем санитизированный патч во временный файл для передачи в PatchApplier
        if not sanitized_patch.endswith("\n"):
            sanitized_patch += "\n"
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, dir=target_dir) as tmp_file:
            tmp_file.write(sanitized_patch)
            temp_patch_path = tmp_file.name

        result = applier.apply_patch(temp_patch_path)
        return result
    except PatchPipelineError:
        raise
    except PatchApplierError as e:
        raise PatchPipelineError(f"Application failed: {e}") from e
    except Exception as e:
        raise PatchPipelineError(f"Unexpected application error: {e}") from e
    finally:
        if temp_patch_path and os.path.exists(temp_patch_path):
            try:
                os.unlink(temp_patch_path)
            except OSError:
                pass


def execute_pipeline(repo_path, patch_source, backup_tag=None):
    """
    Алиас для совместимости с интеграционными тестами.
    """
    return execute_patch_pipeline(repo_path, patch_source, backup_tag=backup_tag)