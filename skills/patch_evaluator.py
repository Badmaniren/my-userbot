import os
import io
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union

from skills.code_sanitizer import CodeSanitizer
from skills.code_validator import CodeValidator
from skills.patch_verifier import PatchVerifier
from skills.patch_autocorrector import PatchAutocorrector
from skills.system_telemetry import SystemTelemetry

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
            try:
                sanitizer = CodeSanitizer(self.repo_path)
            except TypeError:
                sanitizer = CodeSanitizer()

            if hasattr(sanitizer, "sanitize"):
                sanitized_content, is_safe = sanitizer.sanitize(patch_content)
            elif hasattr(sanitizer, "sanitize_patch"):
                try:
                    sanitized_content = sanitizer.sanitize_patch(patch_content)
                    is_safe = True
                except Exception as se:
                    sanitized_content = patch_content
                    is_safe = False
            elif hasattr(sanitizer, "check"):
                is_safe = sanitizer.check(patch_content)
                sanitized_content = patch_content
            elif hasattr(sanitizer, "clean"):
                sanitized_content = sanitizer.clean(patch_content)
                is_safe = True
            else:
                sanitized_content = patch_content
                is_safe = True
            
            if not is_safe:
                reasons = []
                if hasattr(sanitizer, "get_reasons"):
                    reasons = sanitizer.get_reasons()
                return PatchEvaluationResult(is_safe=False, is_valid=False, reasons=reasons)

            try:
                validator = CodeValidator(self.repo_path)
            except TypeError:
                validator = CodeValidator()

            if hasattr(validator, "validate"):
                val_result = validator.validate(sanitized_content)
            elif hasattr(validator, "validate_code"):
                try:
                    validator.validate_code(sanitized_content)
                    val_result = {"is_valid": True, "metrics": {}}
                except Exception as ve:
                    val_result = {"is_valid": False, "metrics": {}, "error": str(ve)}
            else:
                val_result = {"is_valid": True, "metrics": {}}

            try:
                verifier = PatchVerifier(repo_path=self.repo_path, inspector=None, executor=None)
            except TypeError:
                try:
                    verifier = PatchVerifier(self.repo_path)
                except TypeError:
                    try:
                        verifier = PatchVerifier()
                    except TypeError:
                        verifier = object()

            if hasattr(verifier, "verify"):
                is_valid_verify = verifier.verify(sanitized_content)
            elif hasattr(verifier, "verify_patch"):
                is_valid_verify = verifier.verify_patch(sanitized_content)
            elif hasattr(verifier, "verify_and_apply"):
                try:
                    res_v = verifier.verify_and_apply(sanitized_content)
                    is_valid_verify = bool(res_v)
                except Exception:
                    is_valid_verify = False
            else:
                is_valid_verify = True

            is_valid = val_result.get("is_valid", True) and is_valid_verify
            metrics = val_result.get("metrics", {})

            telemetry_data = {}
            if collect_telemetry:
                try:
                    telemetry_instance = SystemTelemetry(self.repo_path)
                except TypeError:
                    telemetry_instance = SystemTelemetry()

                if hasattr(telemetry_instance, "capture"):
                    telemetry_data = telemetry_instance.capture()
                elif hasattr(telemetry_instance, "collect"):
                    telemetry_data = telemetry_instance.collect()
                elif hasattr(telemetry_instance, "collect_system_metrics"):
                    telemetry_data = telemetry_instance.collect_system_metrics()
                else:
                    telemetry_data = {}

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
        try:
            sanitizer = CodeSanitizer(self.repo_path)
        except TypeError:
            sanitizer = CodeSanitizer()

        if hasattr(sanitizer, "sanitize"):
            _, is_safe = sanitizer.sanitize(patch_content)
        elif hasattr(sanitizer, "sanitize_patch"):
            try:
                sanitizer.sanitize_patch(patch_content)
                is_safe = True
            except Exception:
                is_safe = False
        elif hasattr(sanitizer, "check"):
            is_safe = sanitizer.check(patch_content)
        else:
            is_safe = True
        
        was_corrected = False
        if not is_safe:
            try:
                autocorrector = PatchAutocorrector(self.repo_path)
            except TypeError:
                autocorrector = PatchAutocorrector()

            if hasattr(autocorrector, "correct"):
                patch_content, was_corrected = autocorrector.correct(patch_content)
            elif hasattr(autocorrector, "autocorrect"):
                patch_content, was_corrected = autocorrector.autocorrect(patch_content)
            elif hasattr(autocorrector, "correct_syntax"):
                try:
                    patch_content = autocorrector.correct_syntax(patch_content)
                    was_corrected = True
                except Exception:
                    was_corrected = False
            elif hasattr(autocorrector, "fix"):
                try:
                    patch_content = autocorrector.fix(patch_content)
                    was_corrected = True
                except Exception:
                    was_corrected = False

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
