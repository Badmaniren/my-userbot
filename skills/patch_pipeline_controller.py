from typing import Optional
from skills.patch_evaluator import PatchEvaluator, PatchEvaluatorError
from skills.patch_verifier import PatchVerifier, PatchExecutor, PatchExecutorError, LessonParser
from skills.git_inspector import GitInspector


class PatchPipelineControllerError(Exception):
    """Исключение конвейера патчей."""
    pass


class PatchPipelineController:
    """Контроллер для управления конвейером безопасного автоисправления патчей."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self._evaluator = PatchEvaluator(repo_path)
        inspector = GitInspector(repo_path)
        parser = LessonParser(inspector)
        executor = PatchExecutor(repo_path, inspector, parser)
        self._verifier = PatchVerifier(repo_path, inspector, executor)

    def process(self, patch_content: str, target_file: str) -> bool:
        """Оценивает и верифицирует стандартный патч."""
        try:
            eval_result = self._evaluator.evaluate(
                patch_content=patch_content,
                collect_telemetry=True,
                target_file=target_file
            )
        except PatchEvaluatorError as e:
            raise PatchPipelineControllerError(str(e)) from e
        except Exception as e:
            if isinstance(e, PatchPipelineControllerError):
                raise
            raise PatchPipelineControllerError(str(e)) from e

        if not eval_result.is_safe or not eval_result.is_valid:
            return False

        try:
            if target_file:
                return self._verifier.verify_and_apply(patch_content, target_file)
            return self._verifier.verify_and_apply(patch_content)
        except PatchExecutorError as e:
            raise PatchPipelineControllerError(str(e)) from e
        except Exception as e:
            if isinstance(e, PatchPipelineControllerError):
                raise
            raise PatchPipelineControllerError(str(e)) from e

    def process_with_autocorrect(self, patch_content: str, target_file: Optional[str] = None) -> bool:
        """Оценивает с автокоррекцией и верифицирует патч."""
        try:
            eval_result = self._evaluator.evaluate_with_autocorrect(patch_content)
        except PatchEvaluatorError as e:
            raise PatchPipelineControllerError(str(e)) from e
        except Exception as e:
            if isinstance(e, PatchPipelineControllerError):
                raise
            raise PatchPipelineControllerError(str(e)) from e

        if not eval_result.is_safe or not eval_result.is_valid:
            return False

        try:
            if target_file:
                return self._verifier.verify_and_apply(patch_content, target_file)
            return self._verifier.verify_and_apply(patch_content)
        except PatchExecutorError as e:
            raise PatchPipelineControllerError(str(e)) from e
        except Exception as e:
            if isinstance(e, PatchPipelineControllerError):
                raise
            raise PatchPipelineControllerError(str(e)) from e

    def run_pipeline(self, patch_content: str, target_file: str) -> bool:
        """Запускает конвейер (алиас для integration-теста)."""
        return self.process(patch_content, target_file)
