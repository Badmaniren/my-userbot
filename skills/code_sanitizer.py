import ast
import io


class CodeSanitizerError(Exception):
    """Базовое исключение для ошибок санитизации кода."""
    pass


class CodeAntipatternDetectedError(CodeSanitizerError):
    """Исключение, вызываемое при обнаружении запрещенных антипаттернов."""
    pass


class AntipatternVisitor(ast.NodeVisitor):
    def __init__(self, custom_forbidden_patterns=None):
        self.errors = []
        self.custom_forbidden_patterns = custom_forbidden_patterns or []

    def visit_ExceptHandler(self, node):
        if node.body and len(node.body) == 1:
            stmt = node.body[0]
            if isinstance(stmt, ast.Pass):
                # Извлекаем имя исключения, если оно есть, для точного сообщения под тесты
                exc_name = ""
                if node.type:
                    if isinstance(node.type, ast.Name):
                        exc_name = node.type.id
                    elif isinstance(node.type, ast.Attribute):
                        # Для случаев типа modules.Error
                        pass
                
                if exc_name:
                    self.errors.append(f"Обнаружен запрещенный антипаттерн: except {exc_name}: pass")
                else:
                    self.errors.append("Обнаружен запрещенный антипаттерн: except ...: pass")
            elif isinstance(stmt, ast.Continue):
                self.errors.append("Обнаружен запрещенный антипаттерн: except ...: continue")
        self.generic_visit(node)

    def visit_Name(self, node):
        if node.id in self.custom_forbidden_patterns:
            self.errors.append(f"Обнаружен запрещенный паттерн: {node.id}")
        self.generic_visit(node)


class CodeSanitizer:
    def __init__(self, repo_path=None):
        self.repo_path = repo_path
        self.forbidden_patterns = []

    def add_forbidden_pattern(self, pattern: str):
        if pattern not in self.forbidden_patterns:
            self.forbidden_patterns.append(pattern)

    def sanitize_patch(self, code_content: str) -> str:
        # Проверка синтаксиса через ast.parse
        try:
            tree = ast.parse(code_content)
        except SyntaxError as e:
            raise CodeSanitizerError(f"SyntaxError: {e}")

        # Проверка на антипаттерны
        visitor = AntipatternVisitor(self.forbidden_patterns)
        visitor.visit(tree)

        if visitor.errors:
            err_msg = "; ".join(visitor.errors)
            raise CodeAntipatternDetectedError(err_msg)

        return code_content

    def sanitize_stream(self, stream: io.BufferedIOBase) -> str:
        content = stream.read().decode('utf-8')
        return self.sanitize_patch(content)

    def batch_sanitize(self, patch_batch: dict) -> dict:
        results = {}
        for patch_id, code in patch_batch.items():
            try:
                sanitized = self.sanitize_patch(code)
                results[patch_id] = {
                    'is_valid': True,
                    'sanitized_content': sanitized,
                    'error': None
                }
            except (CodeSanitizerError, CodeAntipatternDetectedError) as e:
                results[patch_id] = {
                    'is_valid': False,
                    'sanitized_content': None,
                    'error': str(e)
                }
        return results