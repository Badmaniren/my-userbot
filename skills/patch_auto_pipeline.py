from typing import Any, BinaryIO, Optional
from skills.patch_evaluator import PatchEvaluator
from skills.patch_verifier import PatchVerifier
from skills.patch_executor import PatchExecutor


class PatchAutoPipelineError(Exception):
    """Исключение, возникающее при ошибках в конвейере автоматического исправления патчей."""
    pass


class PipelineResult:
    """Результат выполнения конвейера автоисправления патча."""
    def __init__(self, success: bool, evaluation: Any):
        self.success = success
        self.evaluation = evaluation


class PatchAutoPipeline:
    """Конвейер безопасного автоисправления, объединяющий оценку патчей и их верификацию."""

    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = repo_path
        self.evaluator = PatchEvaluator(repo_path=repo_path)
        executor = PatchExecutor(repo_path=repo_path)
        self.verifier = PatchVerifier(executor=executor, repo_path=repo_path)

    def run(
        self,
        patch_content: str,
        target_file: Optional[str] = None,
        use_autocorrect: bool = False
    ) -> PipelineResult:
        try:
            if use_autocorrect:
                eval_result = self.evaluator.evaluate_with_autocorrect(patch_content)
            else:
                eval_result = self.evaluator.evaluate(
                    patch_content=patch_content,
                    collect_telemetry=True,
                    target_file=target_file
                )

            if not getattr(eval_result, "is_safe", False):
                return PipelineResult(success=False, evaluation=eval_result)

            verification_success = self.verifier.verify_and_apply(patch_content)
            
            success = bool(eval_result.is_safe and verification_success)
            return PipelineResult(success=success, evaluation=eval_result)

        except Exception as e:
            if isinstance(e, PatchAutoPipelineError):
                raise
            raise PatchAutoPipelineError(str(e)) from e

    def run_stream(self, stream_data: BinaryIO) -> PipelineResult:
        try:
            eval_result = self.evaluator.evaluate_stream(stream_data)

            if not getattr(eval_result, "is_safe", False):
                return PipelineResult(success=False, evaluation=eval_result)

            if hasattr(stream_data, "seek"):
                stream_data.seek(0)
            patch_content = stream_data.read()
            if isinstance(patch_content, bytes):
                patch_content = patch_content.decode('utf-8')

            verification_success = self.verifier.verify_and_apply(patch_content)
            
            success = bool(eval_result.is_safe and verification_success)
            return PipelineResult(success=success, evaluation=eval_result)

        except Exception as e:
            if isinstance(e, PatchAutoPipelineError):
                raise
            raise PatchAutoPipelineError(str(e)) from e

    def run_pipeline(self, patch_content: str, target_file: Optional[str] = None) -> bool:
        result = self.run(patch_content, target_file=target_file)
        if not result.success:
            raise PatchAutoPipelineError("Pipeline execution failed validation or verification.")
        return True