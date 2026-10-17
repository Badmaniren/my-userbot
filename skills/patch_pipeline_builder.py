import os
import io

from skills.patch_evaluator import patch_evaluator, PatchEvaluator
from skills.patch_verifier import PatchVerifier
try:
    from skills.code_executor import CodeExecutor
except ImportError:
    CodeExecutor = None


class PatchPipelineError(Exception):
    """Кастомное исключение для ошибок пайплайна верификации патчей."""
    pass


class PatchPipelineBuilder:
    """Сборщик и исполнитель пайплайна верификации патчей на базе оценщика и верификатора."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.evaluator = PatchEvaluator(repo_path=self.repo_path)
        inspector = None
        try:
            from skills.code_inspector import CodeInspector
            inspector = CodeInspector()
        except ImportError:
            inspector = None
        
        executor = CodeExecutor(repo_path=self.repo_path) if CodeExecutor is not None else None
        self.verifier = PatchVerifier(repo_path=self.repo_path, inspector=inspector, executor=executor)

    def run_pipeline(self, patch_content: str, target_file: str) -> bool:
        """Запускает полный пайплайн: оценка безопасности/валидности и верификация (применение)."""
        try:
            eval_result = patch_evaluator(self.repo_path, patch_content, target_file)
        except Exception as e:
            if isinstance(e, PatchPipelineError):
                raise
            raise PatchPipelineError(f"Ошибка в оценщике патча: {e}") from e

        if not getattr(eval_result, "is_safe", True) or not getattr(eval_result, "is_valid", True):
            return False

        try:
            verification_result = self.verifier.verify_and_apply(patch_content)
            return bool(verification_result)
        except Exception as e:
            if isinstance(e, PatchPipelineError):
                raise
            raise PatchPipelineError(f"Ошибка при верификации и применении патча: {e}") from e

    def run_pipeline_stream(self, stream_data: io.BytesIO, target_file: str) -> bool:
        """Запускает пайплайн, принимая содержимое патча в виде байтового потока (stream)."""
        patch_content = stream_data.read().decode("utf-8", errors="ignore")
        return self.run_pipeline(patch_content, target_file)