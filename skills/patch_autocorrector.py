import ast
import io
from skills.patch_verifier import PatchVerifier
from skills.code_sanitizer import CodeSanitizer, AntipatternRemover
from skills.code_validator import CodeValidator

class PatchAutocorrectorError(Exception):
    """Базовое исключение для модуля PatchAutocorrector."""
    pass

class PatchSyntaxError(PatchAutocorrectorError):
    """Исключение при синтаксической ошибке в патче."""
    pass

class PatchAutocorrector:
    def __init__(self, repo_path: str, sanitizer=None, validator=None):
        self.repo_path = repo_path
        self.sanitizer = sanitizer if sanitizer is not None else CodeSanitizer(repo_path=repo_path)
        self.validator = validator if validator is not None else CodeValidator(repo_path=repo_path)

    def correct_syntax(self, code: str) -> str:
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise PatchSyntaxError(f"Invalid syntax: {e}") from e

        forbidden = list(getattr(self.sanitizer, "forbidden_patterns", []))
        remover = AntipatternRemover(custom_forbidden_patterns=forbidden)
        transformed_tree = remover.visit(tree)
        if remover.modified:
            ast.fix_missing_locations(transformed_tree)
            return ast.unparse(transformed_tree)
        return code

    def _apply_transformations(self, code: str) -> str:
        return code

    def transform_stream(self, stream) -> str:
        try:
            content = stream.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8')
        except Exception as e:
            raise PatchAutocorrectorError(f"Failed to read stream: {e}") from e
        
        transformed = self._apply_transformations(content)
        return transformed

    def batch_correct(self, patch_dict: dict) -> dict:
        results = {}
        for key, code in patch_dict.items():
            results[key] = self.correct_syntax(code)
        return results

    def process_and_verify(self, file_name: str, code_fragment: str) -> bool:
        verifier = PatchVerifier(self.repo_path)
        return verifier.verify_and_apply(file_name, code_fragment)

    def correct_and_validate(self, malformed_patch: str) -> str:
        corrected = self.correct_syntax(malformed_patch)
        return corrected
