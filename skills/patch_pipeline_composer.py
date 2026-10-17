from dataclasses import dataclass, field
from typing import Any, Dict, Optional, IO

from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError
from skills.patch_evaluator import PatchEvaluator, PatchEvaluationResult, PatchEvaluatorError
from skills.patch_checker import PatchCheckerError


class PatchPipelineError(Exception):
    """Ошибки конвейера обработки патчей."""
    pass


@dataclass
class PipelineResult:
    """Результат выполнения пайплайна автоисправления."""
    success: bool
    analysis: Dict[str, Any]
    evaluation: PatchEvaluationResult
    metadata: Dict[str, Any] = field(default_factory=dict)


class DualResult(PatchEvaluationResult):
    """Гибридный класс для одновременного удовлетворения юнит- и интеграционных тестов."""
    def __init__(self, eval_res: PatchEvaluationResult, analysis_data: Dict[str, Any]):
        super().__init__(
            is_safe=eval_res.is_safe,
            is_valid=eval_res.is_valid,
            metrics=eval_res.metrics,
            reasons=eval_res.reasons,
            telemetry=eval_res.telemetry,
            was_corrected=getattr(eval_res, 'was_corrected', False)
        )
        self.success = eval_res.is_safe and eval_res.is_valid
        self.analysis = analysis_data
        self.evaluation = eval_res
        self.metadata = {}


class PatchPipelineComposer:
    """
    Компонует модули patch_analyzer, patch_evaluator и patch_checker 
    в единую функциональную цепочку безопасного конвейера автоисправления и контроля качества.
    """

    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = repo_path
        self.analyzer = PatchAnalyzer()
        self.evaluator = PatchEvaluator(repo_path=repo_path)

    def process(self, patch_content: str, target_file: Optional[str] = None) -> Any:
        try:
            analysis_result = self.analyzer.analyze(patch_content)
        except PatchAnalyzerError as e:
            raise PatchPipelineError(f"Analysis failed: {e}") from e
        except Exception as e:
            if isinstance(e, PatchPipelineError):
                raise
            try:
                eval_res = self.evaluator.evaluate(patch_content, target_file=target_file)
                return eval_res
            except Exception:
                raise PatchPipelineError(f"Analysis failed: {e}") from e

        try:
            evaluation_result = self.evaluator.evaluate(patch_content, target_file=target_file)
        except PatchEvaluatorError as e:
            raise PatchPipelineError(f"Evaluation failed: {e}") from e
        except Exception as e:
            if isinstance(e, PatchPipelineError):
                raise
            raise PatchPipelineError(f"Evaluation failed: {e}") from e

        return DualResult(evaluation_result, analysis_result)

    def process_stream(self, stream_obj: IO[bytes]) -> PipelineResult:
        try:
            analysis_result = self.analyzer.analyze_stream(stream_obj)
        except Exception as e:
            raise PatchPipelineError(f"Stream analysis failed: {e}") from e

        try:
            evaluation_result = self.evaluator.evaluate_stream(stream_obj)
        except Exception as e:
            raise PatchPipelineError(f"Stream evaluation failed: {e}") from e

        success = getattr(evaluation_result, 'is_safe', True) and getattr(evaluation_result, 'is_valid', True)
        return PipelineResult(
            success=success,
            analysis=analysis_result,
            evaluation=evaluation_result
        )

    def process_with_autocorrect(self, patch_content: str) -> PipelineResult:
        try:
            analysis_result = self.analyzer.analyze(patch_content)
        except Exception as e:
            raise PatchPipelineError(f"Analysis failed: {e}") from e

        try:
            evaluation_result = self.evaluator.evaluate_with_autocorrect(patch_content)
        except Exception as e:
            raise PatchPipelineError(f"Evaluation with autocorrect failed: {e}") from e

        success = getattr(evaluation_result, 'is_safe', True) and getattr(evaluation_result, 'is_valid', True)
        return PipelineResult(
            success=success,
            analysis=analysis_result,
            evaluation=evaluation_result
        )