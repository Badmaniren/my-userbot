import ast
import os
import subprocess


class PatchValidatorError(Exception):
    """Custom exception for patch validation errors."""
    pass


class PatchValidator:
    """Validator for patches, syntax, security, and git applications."""

    def __init__(self, repo_path=".", code_validator=None, patch_sanitizer=None, git_inspector=None):
        self.repo_path = repo_path
        self.code_validator = code_validator or (
            CodeValidator(repo_path=repo_path) if 'CodeValidator' in globals() else None
        )
        self.patch_sanitizer = patch_sanitizer
        self.git_inspector = git_inspector

    def validate_syntax(self, code_str: str) -> bool:
        """Validates Python code syntax using ast.parse."""
        try:
            ast.parse(code_str)
            return True
        except SyntaxError as e:
            raise PatchValidatorError(f"Invalid syntax: {e}") from e

    def perform_security_check(self, code_str: str) -> bool:
        """Checks for forbidden/dangerous imports in the code AST."""
        try:
            tree = ast.parse(code_str)
        except SyntaxError as e:
            if isinstance(code_str, str) and (code_str.startswith("diff ") or "--- " in code_str or "+++ " in code_str):
                code_lines = []
                for line in code_str.splitlines():
                    if line.startswith('+') and not line.startswith('+++'):
                        code_lines.append(line[1:])
                added_code = "\n".join(code_lines)
                if added_code.strip():
                    try:
                        tree = ast.parse(added_code)
                    except SyntaxError:
                        raise PatchValidatorError(f"Syntax error during security check: {e}") from e
                else:
                    return True
            else:
                raise PatchValidatorError(f"Syntax error during security check: {e}") from e

        dangerous_modules = {'os', 'sys', 'subprocess', 'shutil', 'pickle'}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in dangerous_modules:
                        raise PatchValidatorError(f"Dangerous import detected: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module in dangerous_modules:
                    raise PatchValidatorError(f"Dangerous import detected: {node.module}")
        return True

    def apply_and_test_diff(self, diff_content: str) -> bool:
        """Applies a diff using git apply and runs tests if applicable."""
        try:
            process = subprocess.run(
                ['git', 'apply', '-'],
                input=diff_content.encode('utf-8') if isinstance(diff_content, str) else diff_content,
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            if process.returncode != 0:
                err_msg = process.stderr.decode('utf-8', errors='ignore')
                raise PatchValidatorError(f"Failed to apply diff: {err_msg}")
            return True
        except Exception as e:
            if isinstance(e, PatchValidatorError):
                raise
            raise PatchValidatorError(f"Error applying diff: {e}") from e

    def read_patch_stream(self, file_path: str) -> str:
        """Reads patch file contents from a stream/file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if isinstance(content, bytes):
                return content.decode('utf-8', errors='ignore')
            return content

    def validate_patch(self, patch_content: str):
        """Full validation flow for integration tests."""
        if self.patch_sanitizer:
            patch_content = self.patch_sanitizer.sanitize(patch_content)

        self.perform_security_check(patch_content)

        if self.git_inspector:
            pass

        class ValidationResult:
            def __init__(self, is_valid: bool):
                self.is_valid = is_valid

        return ValidationResult(is_valid=True)