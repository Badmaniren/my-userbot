from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError
from skills.patch_evaluator import PatchEvaluator, PatchEvaluationResult, PatchEvaluatorError

class PatchPipelineError(Exception):
    """Исключение конвейера автоисправления патчей."""
    pass

class PatchPipelineIntegration:
    """
    Интеграционный модуль конвейера безопасного автоисправления, 
    объединяющий анализ, проверку и оценку патчей.
    """
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.analyzer = PatchAnalyzer()
        self.evaluator = PatchEvaluator(repo_path=self.repo_path)

    def run(self, patch_content: str, target_file: str = None) -> PatchEvaluationResult:
        """Запуск конвейера анализа и оценки для текстового патча."""
        try:
            self.analyzer.analyze(patch_content)
        except PatchAnalyzerError as e:
            raise PatchPipelineError(str(e)) from e

        try:
            return self.evaluator.evaluate(
                patch_content=patch_content,
                collect_telemetry=True,
                target_file=target_file
            )
        except PatchEvaluatorError as e:
            raise PatchPipelineError(str(e)) from e

    def run_stream(self, stream) -> PatchEvaluationResult:
        """Запуск конвейера для потоковых данных."""
        self.analyzer.analyze_stream(stream)
        return self.evaluator.evaluate_stream(stream)

    def execute_pipeline(self, patch_content: str, target_file: str = None) -> PatchEvaluationResult:
        """Полное выполнение конвейера с применением патча (интеграционный метод)."""
        return self.run(patch_content, target_file=target_file)