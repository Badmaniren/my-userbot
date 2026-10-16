from skills.code_sanitizer import CodeSanitizer
from skills.code_validator import CodeValidator
from skills.patch_autocorrector import PatchAutocorrector

class PatchManager:
    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path
        self.sanitizer = CodeSanitizer(repo_path=self.repo_path)
        self.validator = CodeValidator(repo_path=self.repo_path)
        self.autocorrector = PatchAutocorrector(repo_path=self.repo_path)

    def process_patch(self, code: str) -> str:
        """
        Комбинирует санитизацию, валидацию и автокоррекцию в единый защищенный пайплайн.
        """
        # Проверяем доступные методы санитизатора для совместимости
        if hasattr(self.sanitizer, 'sanitize_patch'):
            sanitized_code = self.sanitizer.sanitize_patch(code)
        elif hasattr(self.sanitizer, 'sanitize'):
            sanitized_code = self.sanitizer.sanitize(code)
        elif hasattr(self.sanitizer, 'clean'):
            sanitized_code = self.sanitizer.clean(code)
        elif hasattr(self.sanitizer, 'process'):
            sanitized_code = self.sanitizer.process(code)
        else:
            sanitized_code = code

        is_valid = False
        if hasattr(self.validator, 'validate'):
            is_valid = self.validator.validate(sanitized_code)
        elif hasattr(self.validator, 'validate_code'):
            try:
                is_valid = self.validator.validate_code(sanitized_code)
            except Exception:
                is_valid = False
        elif hasattr(self.validator, 'validate_patch_ast'):
            try:
                is_valid = self.validator.validate_patch_ast(sanitized_code)
            except Exception:
                is_valid = False

        if not is_valid:
            if hasattr(self.autocorrector, 'correct'):
                corrected_code = self.autocorrector.correct(sanitized_code)
            elif hasattr(self.autocorrector, 'correct_syntax'):
                corrected_code = self.autocorrector.correct_syntax(sanitized_code)
            elif hasattr(self.autocorrector, 'correct_and_validate'):
                corrected_code = self.autocorrector.correct_and_validate(sanitized_code)
            else:
                corrected_code = sanitized_code

            valid_after_corr = False
            if hasattr(self.validator, 'validate'):
                valid_after_corr = self.validator.validate(corrected_code)
            elif hasattr(self.validator, 'validate_code'):
                try:
                    valid_after_corr = self.validator.validate_code(corrected_code)
                except Exception:
                    valid_after_corr = False

            if not valid_after_corr:
                raise ValueError("Patch validation and correction failed.")
            return corrected_code

        return sanitized_code