from skills.patch_evaluator import PatchEvaluator, PatchEvaluationResult
from skills.git_inspector import GitInspector
from skills.code_sanitizer import CodeSanitizer, CodeSanitizerError, CodeAntipatternDetectedError
from skills.code_validator import CodeValidator, CodeValidatorError


class PatchPipelineError(Exception):
    """Исключение, выбрасываемое при ошибках выполнения конвейера патчей."""
    pass


class PatchPipelineRunner:
    """Конвейер для верификации и применения патчей, объединяющий PatchEvaluator и GitInspector."""

    def __init__(self, repo_path: str, validator=None, autocorrector=None):
        self.repo_path = repo_path
        self.evaluator = PatchEvaluator(repo_path=repo_path)
        self.inspector = GitInspector(repo_path=repo_path)
        self.sanitizer = CodeSanitizer(repo_path=repo_path)
        self.validator = validator if validator is not None else CodeValidator(repo_path=repo_path)
        self.autocorrector = autocorrector

    def run_pipeline(self, patch_content: str, target_file: str):
        try:
            # 1. Анализируем код на антипаттерны и уязвимости через CodeSanitizer и CodeValidator
            sanitized_content = self.sanitizer.sanitize_patch(patch_content)
            self.validator.validate_patch_ast(sanitized_content)

            # 2. Оцениваем патч через PatchEvaluator
            evaluation_result = self.evaluator.evaluate(
                patch_content=patch_content,
                collect_telemetry=True,
                target_file=target_file
            )

            if not evaluation_result.is_safe or not evaluation_result.is_valid:
                raise PatchPipelineError("Patch is unsafe or invalid.")

            class PipelineResult(PatchEvaluationResult):
                def __init__(self, eval_res, history):
                    for attr in dir(eval_res):
                        if not attr.startswith('__'):
                            try:
                                setattr(self, attr, getattr(eval_res, attr))
                            except AttributeError:
                                pass
                    self._commit_history = history

                def get(self, key, default=None):
                    if key == "success":
                        return True
                    if key == "commit_history":
                        return self._commit_history
                    return getattr(self, key, default)

                def __getitem__(self, key):
                    if key == "success":
                        return True
                    if key == "commit_history":
                        return self._commit_history
                    if hasattr(self, key):
                        return getattr(self, key)
                    raise KeyError(key)

            commit_history = self.inspector.get_commit_history()
            return PipelineResult(evaluation_result, commit_history)

        except PatchPipelineError:
            raise
        except (CodeSanitizerError, CodeValidatorError) as e:
            raise PatchPipelineError(f"Patch is unsafe or invalid: {e}") from e
        except Exception as e:
            raise PatchPipelineError(str(e))
