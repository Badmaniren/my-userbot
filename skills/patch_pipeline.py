from skills.code_sanitizer import CodeSanitizer, CodeSanitizerError, CodeAntipatternDetectedError
from skills.code_validator import CodeValidator, CodeValidatorError
from skills.patch_autocorrector import PatchAutocorrector, PatchSyntaxError

class PatchPipeline:
    """
    Пайплайн обработки патчей: санитизация, валидация и автокоррекция.
    """

    def __init__(self, repo_path=None, sanitizer=None, validator=None, autocorrector=None):
        self.repo_path = repo_path
        self.sanitizer = sanitizer or CodeSanitizer(repo_path=repo_path)
        self.validator = validator or CodeValidator(repo_path=repo_path)
        self.autocorrector = autocorrector or PatchAutocorrector(
            repo_path=repo_path,
            sanitizer=self.sanitizer,
            validator=self.validator
        )

    def process(self, code: str) -> str:
        """
        Основной поток обработки: санитизация -> валидация -> (если нужно) автокоррекция.
        """
        try:
            sanitized_code = self.sanitizer.sanitize_patch(code)
        except CodeAntipatternDetectedError:
            return self.autocorrector.correct_and_validate(code)

        try:
            if self.validator.validate_code(sanitized_code):
                return sanitized_code
        except CodeValidatorError:
            pass

        # Если валидация не прошла, запускаем автокоррекцию
        return self.autocorrector.correct_and_validate(sanitized_code)

    def process_stream(self, stream):
        """
        Обработка потока данных через санитизатор.
        """
        return self.sanitizer.sanitize_stream(stream)

    def process_batch(self, patch_batch: dict) -> dict:
        """
        Пакетная обработка словаря патчей.
        """
        raw_results = self.sanitizer.batch_sanitize(patch_batch)
        processed_batch = {}
        for patch_id, result in raw_results.items():
            if isinstance(result, dict):
                if result.get('is_valid') and result.get('sanitized_content') is not None:
                    processed_batch[patch_id] = result['sanitized_content']
                else:
                    # Попробуем обработать исходный патч через process
                    original_code = patch_batch.get(patch_id, "")
                    try:
                        processed_batch[patch_id] = self.process(original_code)
                    except Exception:
                        processed_batch[patch_id] = original_code
            else:
                processed_batch[patch_id] = result
        return processed_batch
