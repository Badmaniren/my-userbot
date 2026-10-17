import ast
import io


class CodeSanitizerError(Exception):
    """Базовое исключение для ошибок санитизации кода."""
    pass


class CodeAntipatternDetectedError(CodeSanitizerError):
    """Исключение, вызываемое при обнаружении запрещенных антипаттернов."""
    pass


class AntipatternRemover(ast.NodeTransformer):
    """Трансформер AST для автоматического удаления/очистки запрещенных антипаттернов."""
    def __init__(self, custom_forbidden_patterns=None):
        super().__init__()
        self.custom_forbidden_patterns = custom_forbidden_patterns or []

    def visit_Expr(self, node):
        self.generic_visit(node)
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name) and node.value.func.id in ('eval', 'exec'):
                return None
        return node

    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id in ('eval', 'exec'):
            return ast.Constant(value=None)
        return node

    def visit_ExceptHandler(self, node):
        self.generic_visit(node)
        if node.body and len(node.body) == 1:
            stmt = node.body[0]
            if isinstance(stmt, (ast.Pass, ast.Continue)):
                node.body = [ast.Expr(value=ast.Constant(value=None))]
        return node


class AntipatternVisitor(ast.NodeVisitor):
    def __init__(self, custom_forbidden_patterns=None):
        self.errors = []
        self.custom_forbidden_patterns = custom_forbidden_patterns or []

    def visit_ExceptHandler(self, node):
        if node.body and len(node.body) == 1:
            stmt = node.body[0]
            if isinstance(stmt, ast.Pass):
                exc_name = ""
                if node.type:
                    if isinstance(node.type, ast.Name):
                        exc_name = node.type.id
                    elif isinstance(node.type, ast.Attribute):
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
        try:
            tree = ast.parse(code_content)
        except SyntaxError as e:
            raise CodeSanitizerError(f"SyntaxError: {e}")

        visitor = AntipatternVisitor(self.forbidden_patterns)
        visitor.visit(tree)

        if visitor.errors:
            if self.repo_path is not None or self.forbidden_patterns:
                err_msg = "; ".join(visitor.errors)
                raise CodeAntipatternDetectedError(err_msg)

        transformer = AntipatternRemover(self.forbidden_patterns)
        transformed_tree = transformer.visit(tree)
        ast.fix_missing_locations(transformed_tree)
        return ast.unparse(transformed_tree)

    def sanitize_stream(self, stream) -> str:
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
            raise CodeSanitizerError("Invalid stream object")
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
