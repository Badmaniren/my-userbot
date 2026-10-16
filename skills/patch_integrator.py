from skills.code_validator import CodeValidator, CodeValidatorError
from skills.patch_autocorrector import PatchAutocorrector, PatchAutocorrectorError


class PatchIntegratorError(Exception):
    """Исключение, возникающее при ошибках интеграции патча."""
    pass


class PatchIntegrator:
    """Конвейер для обработки, автокоррекции и валидации патчей кода."""

    def __init__(self, repo_path=None):
        self.validator = CodeValidator(repo_path=repo_path)
        self.autocorrector = PatchAutocorrector(
            repo_path=repo_path,
            sanitizer=None,
            validator=self.validator
        )

    def integrate_patch(self, file_path, code):
        try:
            corrected_code = self.autocorrector.correct_and_validate(code)
        except PatchAutocorrectorError as e:
            raise PatchIntegratorError(str(e))
        except Exception as e:
            raise PatchIntegratorError(str(e))

        is_valid = self.validator.validate_code(corrected_code)
        if not is_valid:
            raise PatchIntegratorError("Code validation failed after correction.")

        return True

    def integrate_stream(self, stream):
        transformed = self.autocorrector.transform_stream(stream)
        is_valid = self.validator.validate_stream(transformed)
        return is_valid

    def batch_integrate(self, patches_dict):
        corrected_dict = self.autocorrector.batch_correct(patches_dict)
        validation_results = self.validator.batch_validate(corrected_dict)
        return validation_results

    def process_patch(self, file_path, code):
        try:
            corrected_code = self.autocorrector.correct_and_validate(code)
        except Exception as e:
            raise PatchIntegratorError(str(e))

        is_valid = self.validator.validate_code(corrected_code)
        if not is_valid:
            raise PatchIntegratorError("Validation failed")

        repo_p = getattr(self.validator, "repo_path", None)
        if repo_p:
            import os
            full_path = os.path.join(repo_p, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(corrected_code)

        return True