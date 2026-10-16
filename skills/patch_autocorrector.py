import ast
import io
from skills.patch_verifier import PatchVerifier
from skills.code_sanitizer import CodeSanitizer
from skills.code_validator import CodeValidator


class PatchAutocorrectorError(Exception):
    """Базовое исключение для модуля PatchAutocorrector."""
    pass


class PatchSyntaxError(PatchAutocorrectorError):
    """Исключение при синтаксической ошибке в патче."""
    pass


def auto_fix_syntax(code: str) -> str:
    """Пытается исправить простые синтаксические ошибки (например, незакрытые скобки)."""
    chars_to_try = [')', ']', '}', '"', "'"]
    fixed = code
    for _ in range(5):
        try:
            ast.parse(fixed)
            return fixed
        except SyntaxError as e:
            for c in chars_to_try:
                candidate = fixed + c
                try:
                    ast.parse(candidate)
                    return candidate
                except SyntaxError:
                    pass
            lines = fixed.splitlines()
            if lines:
                for c in chars_to_try:
                    lines_copy = list(lines)
                    lines_copy[-1] = lines_copy[-1] + c
                    cand_str = '\n'.join(lines_copy)
                    try:
                        ast.parse(cand_str)
                        return cand_str
                    except SyntaxError:
                        pass
            raise e
    return fixed


class PatchAutocorrector:
    def __init__(self, repo_path: str, sanitizer=None, validator=None):
        self.repo_path = repo_path
        self.sanitizer = sanitizer if sanitizer is not None else CodeSanitizer(repo_path=repo_path)
        self.validator = validator if validator is not None else CodeValidator(repo_path=repo_path)

    def correct_syntax(self, code: str) -> str:
        try:
            ast.parse(code)
        except SyntaxError as e:
            raise PatchSyntaxError(f"Invalid syntax: {e}") from e
        return code

    def _apply_transformations(self, code: str) -> str:
        return code

    def transform_stream(self, stream) -> str:
        try:
            if isinstance(stream, str):
                content = stream
            elif isinstance(stream, bytes):
                content = stream.decode('utf-8', errors='ignore')
            elif hasattr(stream, 'read'):
                if hasattr(stream, 'seek'):
                    try:
                        stream.seek(0)
                    except Exception:
                        pass
                content = stream.read()
                if isinstance(content, bytes):
                    content = content.decode('utf-8', errors='ignore')
            else:
                raise ValueError("Input cannot be read as stream")
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
        try:
            return self.correct_syntax(malformed_patch)
        except PatchSyntaxError:
            try:
                fixed = auto_fix_syntax(malformed_patch)
                return self.correct_syntax(fixed)
            except Exception:
                return self.correct_syntax(malformed_patch)
