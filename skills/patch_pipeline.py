from skills.code_sanitizer import CodeSanitizer, CodeSanitizerError
from skills.code_validator import CodeValidator, CodeValidatorError
from skills.patch_autocorrector import PatchAutocorrector, PatchAutocorrectorError


class PatchPipelineError(Exception):
    """Исключение конвейера обработки патчей."""
    pass


class PatchPipeline:
    def __init__(self, repo_path=None, sanitizer=None, validator=None, autocorrector=None):
        self.repo_path = repo_path
        self.sanitizer = sanitizer if sanitizer is not None else CodeSanitizer(repo_path=repo_path)
        self.validator = validator if validator is not None else CodeValidator(repo_path=repo_path)
        self.autocorrector = autocorrector if autocorrector is not None else PatchAutocorrector(
            repo_path=repo_path,
            sanitizer=self.sanitizer,
            validator=self.validator
        )

    def process_patch(self, raw_code):
        try:
            sanitized_code = self.sanitizer.sanitize_patch(raw_code)
        except CodeSanitizerError as e:
            try:
                corrected_code = self.autocorrector.correct_and_validate(raw_code)
                return corrected_code
            except Exception:
                raise PatchPipelineError(str(e)) from e
        except Exception as e:
            try:
                corrected_code = self.autocorrector.correct_and_validate(raw_code)
                return corrected_code
            except Exception:
                raise PatchPipelineError(str(e)) from e

        try:
            is_valid = self.validator.validate_code(sanitized_code)
        except Exception:
            is_valid = False

        if is_valid:
            return sanitized_code

        try:
            corrected_code = self.autocorrector.correct_and_validate(sanitized_code)
        except PatchAutocorrectorError as e:
            raise PatchPipelineError(str(e)) from e
        except Exception as e:
            raise PatchPipelineError(str(e)) from e

        return corrected_code

    def process_stream(self, stream):
        try:
            sanitized_stream = self.sanitizer.sanitize_stream(stream)
        except Exception as e:
            try:
                return self.autocorrector.transform_stream(stream)
            except Exception as ae:
                raise PatchPipelineError(str(ae)) from ae

        try:
            is_valid = self.validator.validate_stream(sanitized_stream)
        except Exception:
            is_valid = False

        if is_valid:
            return sanitized_stream

        try:
            return self.autocorrector.transform_stream(sanitized_stream)
        except Exception as e:
            raise PatchPipelineError(str(e)) from e

    def batch_process(self, batch_dict):
        result = {}
        for key, val in batch_dict.items():
            result[key] = self.process_patch(val)
        return result
