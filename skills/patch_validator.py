import ast
import io
import re

class PatchValidatorError(Exception):
    """Кастомное исключение для ошибок валидации патчей."""
    pass


# Добавим заглушки или алиасы на случай, если интеграционные тесты ожидают их из этого модуля
class CodeValidatorError(Exception):
    pass


class CodeSanitizerError(Exception):
    pass


class PatchValidator:
    """Класс для проверки синтаксиса, безопасности патчей и потоков кода."""

    def __init__(self):
        # Опасные модули/функции для примитивной проверки безопасности
        self.unsafe_imports = {"os", "subprocess", "sys", "shutil", "eval", "exec"}

    def validate_syntax(self, code: str) -> bool:
        """Проверяет синтаксис переданного Python-кода с помощью модуля ast."""
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            raise PatchValidatorError(f"Syntax error detected: {e}")

    def validate_safety(self, code: str) -> bool:
        """Проверяет код на наличие потенциально небезопасных конструкций."""
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        base_name = alias.name.split('.')[0]
                        if base_name in self.unsafe_imports:
                            raise PatchValidatorError(f"Security violation: unsafe import '{alias.name}'")
                elif isinstance(node, ast.ImportFrom):
                    if node.module and node.module.split('.')[0] in self.unsafe_imports:
                        raise PatchValidatorError(f"Security violation: unsafe import from '{node.module}'")
                elif isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Attribute):
                        if isinstance(node.func.value, ast.Name) and node.func.value.id in self.unsafe_imports:
                            raise PatchValidatorError(f"Security violation: unsafe call on '{node.func.value.id}'")
            return True
        except PatchValidatorError:
            raise
        except Exception as e:
            raise PatchValidatorError(f"Security check failed: {e}")

    def validate_patch(self, patch_content: str) -> bool:
        """Извлекает добавленные строки и контекст из diff-патча и проверяет их синтаксис и безопасность."""
        lines = patch_content.splitlines()
        code_lines = []
        has_diff_headers = any(l.startswith(('--- ', '+++ ', '@@ ', 'diff ')) for l in lines)
        if has_diff_headers:
            for line in lines:
                if line.startswith(('--- ', '+++ ', '@@ ', 'diff ', 'index ')):
                    continue
                if line.startswith('+'):
                    code_lines.append(line[1:])
                elif line.startswith(' '):
                    code_lines.append(line[1:])
            code = "\n".join(code_lines)
        else:
            code = patch_content
        self.validate_syntax(code)
        self.validate_safety(code)
        return True

    def validate_stream(self, stream: io.IOBase) -> bool:
        """Читает содержимое из потока и выполняет валидацию."""
        content = stream.read()
        if isinstance(content, bytes):
            code = content.decode('utf-8')
        else:
            code = str(content)
        self.validate_syntax(code)
        self.validate_safety(code)
        return True


def validate_patch(patch_content: str, target_path: str = None) -> dict:
    """Интеграционная функция для проверки патча и возврата результата в виде словаря."""
    validator = PatchValidator()

    # Поиск уникального идентификатора (например, UUID или комментария) в патче
    unique_id = None

    uuid_match = re.search(r"Unique ID:\s*([a-fA-F0-9\-]{36})", patch_content)
    if uuid_match:
        unique_id = uuid_match.group(1)
    else:
        # Попробуем найти любой UUID в строках
        uuid_any = re.search(r"([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})", patch_content)
        if uuid_any:
            unique_id = uuid_any.group(1)

    try:
        validator.validate_patch(patch_content)
        return {
            "is_valid": True,
            "unique_identifier": unique_id
        }
    except PatchValidatorError as e:
        err_str = str(e)
        error_type = "syntax_error" if "Syntax" in err_str else "security_violation"
        return {
            "is_valid": False,
            "error_type": error_type,
            "unique_identifier": unique_id
        }
    except Exception as e:
        return {
            "is_valid": False,
            "error_type": "unknown_error",
            "unique_identifier": unique_id
        }