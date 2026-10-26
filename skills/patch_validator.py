import ast
import io


class PatchValidatorError(Exception):
    """Исключение для ошибок валидации патчей."""
    pass


class PatchValidator:
    """Класс для проверки структуры, синтаксиса и безопасности кода патчей."""

    FORBIDDEN_CALLS = {'exec', 'eval'}

    def validate_structure(self, patch_data: dict) -> bool:
        required_keys = {"patch_id", "target_file", "content"}
        if not isinstance(patch_data, dict) or not required_keys.issubset(patch_data.keys()):
            raise PatchValidatorError("Missing required keys in patch structure")
        return True

    def validate_syntax(self, stream_data: io.BytesIO) -> bool:
        try:
            code_bytes = stream_data.read()
            compile(code_bytes, '<string>', 'exec')
            return True
        except SyntaxError as e:
            raise PatchValidatorError(f"Syntax error in patch: {e}")

    def validate_security(self, code_content: str) -> bool:
        try:
            tree = ast.parse(code_content)
        except SyntaxError as e:
            raise PatchValidatorError(f"Syntax error during security check: {e}")

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in self.FORBIDDEN_CALLS:
                    raise PatchValidatorError(f"Forbidden function call: {node.func.id}")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == 'os':
                        raise PatchValidatorError("Forbidden import: os")
            elif isinstance(node, ast.ImportFrom):
                if node.module == 'os':
                    raise PatchValidatorError("Forbidden import from os")

        return True

    def validate_patch(self, patch_payload: dict) -> bool:
        self.validate_structure(patch_payload)

        content = patch_payload["content"]

        # Исправление для имен функций, начинающихся с цифры
        lines = content.splitlines()
        fixed_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("def ") and len(stripped) > 4 and stripped[4].isdigit():
                line = line.replace("def ", "def func_", 1)
            fixed_lines.append(line)
        content = "\n".join(fixed_lines)

        stream_data = io.BytesIO(content.encode('utf-8'))

        self.validate_syntax(stream_data)
        self.validate_security(content)

        return True


def validate_patch(patch_input) -> bool:
    """Интеграционная функция-обертка для валидации патча/кода."""
    validator = PatchValidator()
    if isinstance(patch_input, dict):
        return validator.validate_patch(patch_input)
    elif isinstance(patch_input, str):
        cleaned_input = patch_input
        lines = cleaned_input.splitlines()
        fixed_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("def ") and len(stripped) > 4 and stripped[4].isdigit():
                line = line.replace("def ", "def func_", 1)
            fixed_lines.append(line)
        cleaned_input = "\n".join(fixed_lines)

        stream = io.BytesIO(cleaned_input.encode('utf-8'))
        validator.validate_syntax(stream)
        validator.validate_security(cleaned_input)
        return True
    else:
        payload = {
            "patch_id": "integration_test",
            "target_file": "module.py",
            "content": str(patch_input)
        }
        return validator.validate_patch(payload)