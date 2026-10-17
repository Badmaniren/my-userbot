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
            result = self.patch_evaluator.evaluate(
                patch_content=patch_content,
                target_file=target_file,
                collect_telemetry=True
            )
            if patch_content and target_file:
                target_path = f"{self.repo_path}/{target_file}" if not target_file.startswith(self.repo_path) else target_file
                try:
                    with open(target_path, "a", encoding="utf-8") as f:
                        f.write("\n" + patch_content if not patch_content.startswith("\n") else patch_content)
                except IOError as io_err:
                    raise PatchPipelineError(f"Failed to write patch content to target file: {io_err}") from io_err
            return result
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