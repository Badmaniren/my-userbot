import io
import os
from typing import Any, Dict, Optional, Union

from skills.patch_analyzer import PatchAnalyzer, PatchAnalyzerError
from skills.patch_evaluator import PatchEvaluationResult, PatchEvaluator, PatchEvaluatorError


class PatchCheckerError(Exception):
    """Исключение, возникающее при ошибках проверки патча."""
    pass


class PatchChecker:
    """Интегрированный модуль проверки патчей."""

    def __init__(self, repo_path: Optional[str] = None, policy: Optional[Dict[str, Any]] = None):
        self.repo_path = repo_path
        self.policy = policy or {}
        self.analyzer = PatchAnalyzer()
        self.evaluator = PatchEvaluator(repo_path=repo_path)

    def check_patch(self, patch_content: str, target_file: Optional[str] = None) -> Dict[str, Any]:
        if not isinstance(patch_content, str) or not patch_content or not patch_content.strip():
            raise PatchCheckerError("Пустой или некорректный патч не может быть обработан.")

        try:
            analysis_data = self.analyzer.analyze(patch_content)
        except PatchAnalyzerError as e:
            raise PatchCheckerError(f"Ошибка анализатора: {e}") from e

        try:
            evaluation_result = self.evaluator.evaluate(
                patch_content=patch_content,
                target_file=target_file
            )
        except PatchEvaluatorError as e:
            raise PatchCheckerError(f"Ошибка оценщика: {e}") from e

        is_safe = getattr(evaluation_result, "is_safe", True)
        is_valid = getattr(evaluation_result, "is_valid", True)
        metrics = getattr(evaluation_result, "metrics", {})
        reasons = getattr(evaluation_result, "reasons", [])
        telemetry = getattr(evaluation_result, "telemetry", {})
        was_corrected = getattr(evaluation_result, "was_corrected", False)

        risk_score = analysis_data.get("risk_score", 0.0)

        policy_verdict = {}
        if self.policy:
            if self.policy.get("strict_safety") and not is_safe:
                policy_verdict["disallowed_risks"] = "Strict safety policy violated"
            if self.policy.get("disallow_syntax_risks") and analysis_data.get("syntax_risks"):
                policy_verdict["disallowed_risks"] = "Syntax risks detected"
            max_risk = self.policy.get("max_risk_score")
            if max_risk is not None and risk_score > max_risk:
                policy_verdict["disallowed_risks"] = f"Risk score {risk_score} exceeds maximum allowed {max_risk}"

        return {
            "is_safe": is_safe,
            "is_valid": is_valid,
            "risk_score": risk_score,
            "analysis": analysis_data,
            "evaluation": {
                "is_safe": is_safe,
                "is_valid": is_valid,
                "metrics": metrics,
                "reasons": reasons,
                "telemetry": telemetry,
                "was_corrected": was_corrected,
            },
            "policy_verdict": policy_verdict,
        }

    def check_file(self, file_path: str, target_file: Optional[str] = None) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise PatchCheckerError(f"Файл не найден: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            raise PatchCheckerError(f"Не удалось прочитать файл {file_path}: {e}") from e

        return self.check_patch(patch_content=content, target_file=target_file)

    def check_stream(self, stream: io.TextIOBase, target_file: Optional[str] = None) -> Dict[str, Any]:
        try:
            content = stream.read()
        except Exception as e:
            raise PatchCheckerError(f"Не удалось прочитать поток: {e}") from e

        return self.check_patch(patch_content=content, target_file=target_file)

    def check(self, patch_content: str, repo_path: Optional[str] = None, target_file: Optional[str] = None) -> Dict[str, Any]:
        """Интеграционный метод проверки, поддерживающий передачу repo_path на лету."""
        if repo_path and repo_path != self.repo_path:
            self.repo_path = repo_path
            self.evaluator = PatchEvaluator(repo_path=repo_path)
        
        result = self.check_patch(patch_content=patch_content, target_file=target_file)
        
        if "evaluation" in result and "metrics" in result["evaluation"]:
            result["metrics"] = result["evaluation"]["metrics"]
            
        return result


def check_patch(patch_content: str, repo_path: Optional[str] = None, target_file: Optional[str] = None, policy: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    checker = PatchChecker(repo_path=repo_path, policy=policy)
    return checker.check_patch(patch_content=patch_content, target_file=target_file)