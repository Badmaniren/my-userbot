from skills.patch_evaluator import PatchEvaluator, PatchEvaluatorError
from skills.patch_verifier import PatchVerifier, PatchExecutorError
from skills.code_inspector import CodeInspector
from skills.patch_executor import PatchExecutor


class PatchPipelineControllerError(Exception):
    """Исключение конвейера патчей."""
    pass


class PatchPipelineController:
    """Контроллер для управления конвейером безопасного автоисправления патчей."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self._evaluator = PatchEvaluator(repo_path)
        self._inspector = CodeInspector()
        self._executor = PatchExecutor(repo_path)
        self._verifier = PatchVerifier(self._inspector, self._executor)

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

        if not eval_result.is_safe or not eval_result.is_valid:
            return False

        try:
            return self._verifier.verify_and_apply(patch_content)
        except PatchExecutorError as e:
            raise PatchPipelineControllerError(str(e)) from e

    def process_with_autocorrect(self, patch_content: str) -> bool:
        """Оценивает с автокоррекцией и верифицирует патч."""
        try:
            eval_result = self._evaluator.evaluate_with_autocorrect(patch_content)
        except PatchEvaluatorError as e:
            raise PatchPipelineControllerError(str(e)) from e

        if not eval_result.is_safe or not eval_result.is_valid:
            return False

        try:
            return self._verifier.verify_and_apply(patch_content)
        except PatchExecutorError as e:
            raise PatchPipelineControllerError(str(e)) from e

    def run_pipeline(self, patch_content: str, target_file: str) -> bool:
        """Запускает конвейер (алиас для integration-теста)."""
        return self.process(patch_content, target_file)