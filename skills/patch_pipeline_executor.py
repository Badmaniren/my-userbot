from skills.git_inspector import GitInspector
from skills.patch_evaluator import PatchEvaluator, PatchEvaluationResult


class PatchPipelineError(Exception):
    """Исключение, возникающее при ошибках в работе конвейера автоисправления."""
    pass


class PatchPipelineExecutor:
    """Конвейер автоисправления: объединяет GitInspector и PatchEvaluator."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.git_inspector = GitInspector(repo_path)
        self.patch_evaluator = PatchEvaluator(repo_path=repo_path)

    def execute(self, patch_content: str, target_file: str) -> PatchEvaluationResult:
        try:
            self.git_inspector.analyze_repository()
            return self.patch_evaluator.evaluate(
                patch_content=patch_content,
                target_file=target_file,
                collect_telemetry=True
            )
        except Exception as e:
            if isinstance(e, PatchPipelineError):
                raise
            raise PatchPipelineError(str(e)) from e

    def execute_with_autocorrect(self, patch_content: str) -> PatchEvaluationResult:
        try:
            self.git_inspector.analyze_repository()
            return self.patch_evaluator.evaluate_with_autocorrect(patch_content)
        except Exception as e:
            if isinstance(e, PatchPipelineError):
                raise
            raise PatchPipelineError(str(e)) from e

    def execute_stream(self, stream) -> PatchEvaluationResult:
        try:
            self.git_inspector.analyze_repository()
            return self.patch_evaluator.evaluate_stream(stream)
        except Exception as e:
            if isinstance(e, PatchPipelineError):
                raise
            raise PatchPipelineError(str(e)) from e