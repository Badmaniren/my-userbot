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

class PatchAutocorrector:
    def __init__(self, repo_path: str = None, sanitizer=None, validator=None):
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

    def fix(self, code: str, error_msg: str = "") -> str:
        import re
        lines = code.splitlines(keepends=True)
        fixed_lines = []
        for line in lines:
            # Fix unclosed parenthesis
            if line.count('(') > line.count(')'):
                diff = line.count('(') - line.count(')')
                line = line.rstrip('\r\n') + (')' * diff) + ('\n' if line.endswith('\n') else '')
            # Fix bare except
            line = re.sub(r'(\b)except\s*:', r'\1except Exception as e:', line)
            fixed_lines.append(line)
        fixed_code = "".join(fixed_lines)
        fixed_code = re.sub(r'except Exception as e:\s*\n(\s*)pass', r'except Exception as e:\n\1print(f"Error: {e}")', fixed_code)
        return fixed_code

    def correct_and_validate(self, malformed_patch: str) -> str:
        corrected = self.correct_syntax(malformed_patch)
        return corrected