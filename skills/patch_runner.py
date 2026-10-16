from skills.code_validator import CodeValidator, CodeValidatorASTError
from skills.patch_autocorrector import PatchAutocorrector, PatchAutocorrectorError
from skills.patch_executor import PatchExecutor, PatchExecutorError


class PatchRunnerError(Exception):
    """Исключение, возникающее при ошибках в пайплайне PatchRunner."""
    pass


class PatchRunner:
    def __init__(self, repo_path=None, validator=None, autocorrector=None, executor=None):
        self.repo_path = repo_path

        if validator is not None:
            self.validator = validator
        else:
            self.validator = CodeValidator(repo_path=repo_path)

        if autocorrector is not None:
            self.autocorrector = autocorrector
        else:
            self.autocorrector = PatchAutocorrector(repo_path=repo_path, validator=self.validator)

        if executor is not None:
            self.executor = executor
        else:
            self.executor = PatchExecutor(repo_path=repo_path)

    def run_pipeline(self, patch_payload):
        code_key = "code" if "code" in patch_payload else "content"
        code = patch_payload.get(code_key)

        try:
            try:
                is_valid = self.validator.validate_code(code)
            except CodeValidatorASTError:
                is_valid = False

            if not is_valid:
                try:
                    corrected_code = self.autocorrector.correct_and_validate(code)
                except Exception as e:
                    raise PatchAutocorrectorError(str(e))

                patch_payload = patch_payload.copy()
                patch_payload[code_key] = corrected_code
                if "code" in patch_payload and "content" in patch_payload:
                    patch_payload["code"] = corrected_code

            result = self.executor.apply_patch(patch_payload)
            return result
        except (PatchAutocorrectorError, PatchExecutorError) as e:
            raise PatchRunnerError(str(e))

    def process_stream(self, stream):
        try:
            is_valid = self.validator.validate_stream(stream)
        except Exception:
            is_valid = False

        if not is_valid:
            if hasattr(stream, "seek"):
                stream.seek(0)
            transformed = self.autocorrector.transform_stream(stream)
            return transformed
        else:
            if hasattr(stream, "seek"):
                stream.seek(0)
            return stream.read().decode('utf-8')