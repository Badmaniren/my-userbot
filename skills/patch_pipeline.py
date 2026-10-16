from skills.code_sanitizer import CodeSanitizer, CodeSanitizerError
from skills.code_validator import CodeValidator, CodeValidatorASTError, CodeValidatorError
from skills.patch_autocorrector import PatchAutocorrector


class PatchPipeline:
    def __init__(self, repo_path=None, sanitizer=None, validator=None, autocorrector=None):
        self.repo_path = repo_path
        self.sanitizer = sanitizer if sanitizer is not None else CodeSanitizer(repo_path=repo_path)
        self.validator = validator if validator is not None else CodeValidator(repo_path=repo_path)
        self.autocorrector = autocorrector if autocorrector is not None else PatchAutocorrector(
            repo_path=self.repo_path,
            sanitizer=self.sanitizer,
            validator=self.validator
        )

    def process_patch(self, patch_code):
        if isinstance(patch_code, dict):
            return self.batch_process(patch_code)

        try:
            sanitized = self.sanitizer.sanitize_patch(patch_code)
        except (SyntaxError, CodeValidatorASTError, CodeValidatorError, CodeSanitizerError):
            sanitized = patch_code

        if isinstance(sanitized, dict):
            return self.batch_process(sanitized)

        try:
            is_valid = self.validator.validate_code(sanitized)
        except (SyntaxError, CodeValidatorASTError, CodeValidatorError):
            is_valid = False

        if is_valid:
            return sanitized

        return self.autocorrector.correct_and_validate(sanitized)

    def process(self, patch_code):
        return self.process_patch(patch_code)

    def process_stream(self, stream):
        sanitized = self.sanitizer.sanitize_stream(stream)
        try:
            if self.validator.validate_stream(sanitized):
                return sanitized
        except (SyntaxError, CodeValidatorASTError, CodeValidatorError):
            pass
        return sanitized

    def batch_process(self, batch_input):
        try:
            sanitized_batch = self.sanitizer.batch_sanitize(batch_input)
        except (SyntaxError, CodeValidatorASTError, CodeValidatorError, CodeSanitizerError):
            sanitized_batch = batch_input

        result = {}
        if isinstance(sanitized_batch, dict):
            for key, item in sanitized_batch.items():
                if isinstance(item, dict) and "sanitized_content" in item:
                    if item.get("is_valid") and item.get("sanitized_content") is not None:
                        code = item["sanitized_content"]
                    else:
                        code = batch_input.get(key, item)
                else:
                    code = item

                if isinstance(code, dict):
                    result[key] = self.batch_process(code)
                    continue

                try:
                    is_valid = self.validator.validate_code(code)
                except (SyntaxError, CodeValidatorASTError, CodeValidatorError):
                    is_valid = False

                if is_valid:
                    result[key] = code
                else:
                    result[key] = self.autocorrector.correct_and_validate(code)
        return result