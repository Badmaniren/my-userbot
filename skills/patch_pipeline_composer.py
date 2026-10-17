from typing import Any, Dict, Optional, IO

from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError
from skills.patch_evaluator import PatchEvaluator, PatchEvaluationResult, PatchEvaluatorError
from skills.patch_checker import PatchChecker, PatchCheckerError


class PatchPipelineError(Exception):
    """Ошибки конвейера обработки патчей."""
    pass


class PipelineResult(PatchEvaluationResult):
    """Результат выполнения пайплайна автоисправления."""
    def __init__(
        self,
        success: bool,
        analysis: Dict[str, Any],
        evaluation: PatchEvaluationResult,
        metadata: Optional[Dict[str, Any]] = None
    ):
        is_safe = getattr(evaluation, "is_safe", True)
        analysis_valid = analysis.get("is_valid", True) if isinstance(analysis, dict) else True
        if isinstance(analysis, dict) and ("files" in analysis or "parsed" in analysis or "statistics" in analysis):
            has_parsed_data = bool(
                analysis.get("files") or
                analysis.get("chunks") or
                (analysis.get("statistics", {}).get("total_changes", 0) > 0)
            )
            if not has_parsed_data:
                analysis_valid = False

        eval_valid = getattr(evaluation, "is_valid", True)
        is_valid = analysis_valid and eval_valid
        metrics = getattr(evaluation, "metrics", {})
        reasons = getattr(evaluation, "reasons", [])
        if isinstance(analysis, dict) and "errors" in analysis and analysis["errors"]:
            reasons = list(reasons) + analysis["errors"]
        telemetry = getattr(evaluation, "telemetry", {})
        was_corrected = getattr(evaluation, "was_corrected", False)

        super().__init__(
            is_safe=is_safe,
            is_valid=is_valid,
            metrics=metrics,
            reasons=reasons,
            telemetry=telemetry,
            was_corrected=was_corrected
        )
        self.success = success
        self.analysis = analysis
        self.evaluation = evaluation
        self.metadata = metadata or {}


class PatchPipelineComposer:
    """
    Компонует модули patch_analyzer, patch_evaluator и patch_checker
    в единую функциональную цепочку безопасного конвейера автоисправления и контроля качества.
    """

    def __init__(self, repo_path: Optional[str] = None):
        self.repo_path = repo_path
        self._analyzer = None
        self._evaluator = None
        self._checker = None

    @property
    def analyzer(self) -> PatchAnalyzer:
        if self._analyzer is None:
            return PatchAnalyzer()
        return self._analyzer

    @analyzer.setter
    def analyzer(self, value: PatchAnalyzer):
        self._analyzer = value

    @property
    def evaluator(self) -> PatchEvaluator:
        if self._evaluator is None:
            return PatchEvaluator(repo_path=self.repo_path)
        return self._evaluator

    @evaluator.setter
    def evaluator(self, value: PatchEvaluator):
        self._evaluator = value

    @property
    def checker(self) -> PatchChecker:
        if self._checker is None:
            return PatchChecker(repo_path=self.repo_path)
        return self._checker

    @checker.setter
    def checker(self, value: PatchChecker):
        self._checker = value

    def process(self, patch_content: str, target_file: Optional[str] = None) -> PipelineResult:
        try:
            analysis_result = self.analyzer.analyze(patch_content)
        except PatchAnalyzerError as e:
            raise PatchPipelineError(f"Analysis failed: {e}") from e

        try:
            evaluation_result = self.evaluator.evaluate(patch_content, target_file=target_file)
        except PatchEvaluatorError as e:
            raise PatchPipelineError(f"Evaluation failed: {e}") from e

        checker_result = {}
        try:
            checker_result = self.checker.check_patch(patch_content, target_file=target_file)
        except PatchCheckerError:
            checker_result = {"is_safe": False, "is_valid": False}

        is_safe = getattr(evaluation_result, "is_safe", True) and checker_result.get("is_safe", True)
        analysis_valid = analysis_result.get("is_valid", True) if isinstance(analysis_result, dict) else True
        if isinstance(analysis_result, dict) and ("files" in analysis_result or "parsed" in analysis_result or "statistics" in analysis_result):
            has_parsed_data = bool(
                analysis_result.get("files") or
                analysis_result.get("chunks") or
                (analysis_result.get("statistics", {}).get("total_changes", 0) > 0)
            )
            if not has_parsed_data:
                analysis_valid = False

        checker_valid = checker_result.get("is_valid", True) if isinstance(checker_result, dict) and "is_valid" in checker_result else True
        is_valid = getattr(evaluation_result, "is_valid", True) and analysis_valid and checker_valid
        success = is_safe and is_valid

        metadata = {}
        if checker_result.get("policy_verdict"):
            metadata["policy_verdict"] = checker_result["policy_verdict"]

        return PipelineResult(
            success=success,
            analysis=analysis_result,
            evaluation=evaluation_result,
            metadata=metadata
        )

    def process_stream(self, stream_obj: IO[bytes]) -> PipelineResult:
        try:
            analysis_result = self.analyzer.analyze_stream(stream_obj)
        except PatchAnalyzerError as e:
            raise PatchPipelineError(f"Stream analysis failed: {e}") from e

        try:
            evaluation_result = self.evaluator.evaluate_stream(stream_obj)
        except PatchEvaluatorError as e:
            raise PatchPipelineError(f"Stream evaluation failed: {e}") from e

        is_safe = getattr(evaluation_result, 'is_safe', True)
        analysis_valid = analysis_result.get("is_valid", True) if isinstance(analysis_result, dict) else True
        is_valid = getattr(evaluation_result, 'is_valid', True) and analysis_valid
        success = is_safe and is_valid

        return PipelineResult(
            success=success,
            analysis=analysis_result,
            evaluation=evaluation_result
        )

    def process_with_autocorrect(self, patch_content: str) -> PipelineResult:
        try:
            analysis_result = self.analyzer.analyze(patch_content)
        except PatchAnalyzerError as e:
            raise PatchPipelineError(f"Analysis failed: {e}") from e

        try:
            evaluation_result = self.evaluator.evaluate_with_autocorrect(patch_content)
        except PatchEvaluatorError as e:
            raise PatchPipelineError(f"Evaluation failed: {e}") from e

        is_safe = getattr(evaluation_result, 'is_safe', True)
        analysis_valid = analysis_result.get("is_valid", True) if isinstance(analysis_result, dict) else True
        is_valid = getattr(evaluation_result, 'is_valid', True) and analysis_valid
        success = is_safe and is_valid

        return PipelineResult(
            success=success,
            analysis=analysis_result,
            evaluation=evaluation_result
        )