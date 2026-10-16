from skills.code_sanitizer import CodeSanitizer, CodeSanitizerError
from skills.code_validator import CodeValidator, CodeValidatorError
from skills.patch_autocorrector import PatchAutocorrector, PatchAutocorrectorError

class PatchPipelineError(Exception):
    """Базовое исключение для ошибок конвейера патчей."""
    pass

class PatchPipeline:
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.sanitizer = CodeSanitizer(repo_path=self.repo_path)
        self.validator = CodeValidator(repo_path=self.repo_path)
        self.autocorrector = PatchAutocorrector(
            repo_path=self.repo_path,
            sanitizer=self.sanitizer,
            validator=self.validator
        )

    def process_patch(self, patch_code: str) -> str:
        try:
            sanitized_code = self.sanitizer.sanitize_patch(patch_code)
        except CodeSanitizerError as e:
            raise PatchPipelineError(str(e))

        try:
            if self.validator.validate_code(sanitized_code):
                return sanitized_code
        except CodeValidatorError:
            # Если валидация не прошла, пробуем автокоррекцию
            pass

        try:
            return self.autocorrector.correct_and_validate(sanitized_code)
        except PatchAutocorrectorError as e:
            raise PatchPipelineError(f"Автокоррекция не смогла исправить код: {str(e)}")

    def process_stream(self, stream) -> str:
        try:
            sanitized_code = self.sanitizer.sanitize_stream(stream)
            self.validator.validate_stream(sanitized_code)
            return sanitized_code
        except (CodeSanitizerError, CodeValidatorError) as e:
            raise PatchPipelineError(str(e))

    def batch_process(self, batch_data: dict) -> dict:
        try:
            sanitized_batch = self.sanitizer.batch_sanitize(batch_data)
            clean_batch = {}
            for key, val in sanitized_batch.items():
                if isinstance(val, dict):
                    if not val.get('is_valid', True) or val.get('error'):
                        raise CodeSanitizerError(val.get('error') or f"Некорректный код для ключа {key}")
                    code = val.get('sanitized_content')
                else:
                    code = val

                if not isinstance(code, str):
                    raise PatchPipelineError(f"Некорректный формат кода для ключа {key}")
                clean_batch[key] = code

            val_res = self.validator.batch_validate(clean_batch)
            if isinstance(val_res, dict) and val_res.get("failed"):
                raise CodeValidatorError(f"Ошибка валидации пакета для ключей: {val_res['failed']}")
            return clean_batch
        except (CodeSanitizerError, CodeValidatorError) as e:
            raise PatchPipelineError(str(e))