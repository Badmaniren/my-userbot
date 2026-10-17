import os
import io
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

class PatchEvaluatorError(Exception):
    """Исключение для ошибок модуля оценки патчей."""
    pass

class PatchEvaluationResult:
    """Результат оценки патча."""
    def __init__(
        self,
        is_safe: bool = True,
        is_valid: bool = True,
        metrics: Optional[Dict[str, Any]] = None,
        reasons: Optional[List[str]] = None,
        telemetry: Optional[Dict[str, Any]] = None,
        was_corrected: bool = False
    ):
        self.is_safe = is_safe
        self.is_valid = is_valid
        self.metrics = metrics or {}
        self.reasons = reasons or []
        self.telemetry = telemetry or {}
        self.was_corrected = was_corrected

class CodeSanitizer:
    def __init__(self):
        self._reasons: List[str] = []

    def sanitize(self, patch_content: str) -> Tuple[str, bool]:
        self._reasons = []
        unsafe_keywords = ["os.system", "rm -rf", "exec(", "eval(", "subprocess", "shutil.rmtree"]
        for kw in unsafe_keywords:
            if kw in patch_content:
                self._reasons.append(f"Обнаружен опасный код или команда: {kw}")
                return patch_content, False
        return patch_content, True
    
    def get_reasons(self) -> List[str]:
        return self._reasons

class CodeValidator:
    def validate(self, patch_content: str) -> Dict[str, Any]:
        return {"is_valid": True, "metrics": {}}

class PatchVerifier:
    def verify(self, patch_content: str) -> bool:
        return True

class PatchAutocorrector:
    def correct(self, patch_content: str) -> Tuple[str, bool]:
        return patch_content, True

class SystemTelemetry:
    def capture(self) -> Dict[str, Any]:
        return {"snapshot_id": "dummy_snapshot"}

class PatchEvaluator:
    """Модуль для автоматической оценки качества и безопасности патчей."""
    def __init__(self, repo_path: Union[str, Path]):
        self.repo_path = str(repo_path)

    def evaluate(
        self,
        patch_content: str,
        collect_telemetry: bool = False,
        target_file: Optional[str] = None
    ) -> PatchEvaluationResult:
        try:
            sanitizer = CodeSanitizer()
            sanitized_content, is_safe = sanitizer.sanitize(patch_content)
            
            if not is_safe:
                reasons = sanitizer.get_reasons()
                return PatchEvaluationResult(is_safe=False, is_valid=False, reasons=reasons)

            validator = CodeValidator()
            val_result = validator.validate(sanitized_content)

            verifier = PatchVerifier()
            is_valid_verify = verifier.verify(sanitized_content)

            is_valid = val_result.get("is_valid", True) and is_valid_verify
            metrics = val_result.get("metrics", {})

            telemetry_data = {}
            if collect_telemetry:
                telemetry_data = SystemTelemetry().capture()

            return PatchEvaluationResult(
                is_safe=True,
                is_valid=is_valid,
                metrics=metrics,
                telemetry=telemetry_data
            )
        except Exception as e:
            if isinstance(e, PatchEvaluatorError):
                raise
            raise PatchEvaluatorError(str(e))

    def evaluate_with_autocorrect(self, patch_content: str) -> PatchEvaluationResult:
        sanitizer = CodeSanitizer()
        _, is_safe = sanitizer.sanitize(patch_content)
        
        was_corrected = False
        if not is_safe:
            autocorrector = PatchAutocorrector()
            patch_content, was_corrected = autocorrector.correct(patch_content)

        result = self.evaluate(patch_content)
        result.was_corrected = was_corrected
        return result

    def evaluate_stream(self, stream: io.BytesIO) -> PatchEvaluationResult:
        content = stream.read().decode('utf-8')
        return self.evaluate(content)

def patch_evaluator(
    repo_path: Union[str, Path],
    patch_data: str,
    target_file: Optional[str] = None
) -> PatchEvaluationResult:
    evaluator = PatchEvaluator(repo_path=repo_path)
    return evaluator.evaluate(patch_data, target_file=target_file)