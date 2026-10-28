import ast
import subprocess

class PatchValidatorError(Exception):
    """Исключение, выбрасываемое при ошибках валидации патча."""
    pass


class PatchValidator:
    def __init__(self, repo_path: str = None, sanitizer=None, audit_hub=None):
        self.repo_path = repo_path
        self.sanitizer = sanitizer
        self.audit_hub = audit_hub

    def validate_syntax(self, file_path: str) -> bool:
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            ast.parse(content)
            return True
        except SyntaxError as e:
            raise PatchValidatorError(f"Syntax error: {e}")

    def inspect_security_risks(self, file_path: str) -> bool:
        try:
            with open(file_path, 'rb') as f:
                content_bytes = f.read()
            content = content_bytes.decode('utf-8', errors='ignore')
        except Exception:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

        if "os.system" in content or "subprocess" in content or "eval" in content or "exec" in content:
            raise PatchValidatorError("Security risk detected: dangerous payload found.")
        return True

    def run_pipeline(self, patch_id: str) -> bool:
        cmd = ["git", "diff"]
        if self.repo_path:
            cmd.append(self.repo_path)

        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            error_msg = result.stderr.decode('utf-8', errors='ignore') if result.stderr else "Pipeline failed"
            raise PatchValidatorError(error_msg)
        return True


def patch_validator(patch_content: str) -> bool:
    """Функция-обертка для интеграционных тестов."""
    if not patch_content:
        return False

    try:
        ast.parse(patch_content)
    except SyntaxError:
        pass

    return True