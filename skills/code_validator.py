import ast
import os


class CodeValidatorError(Exception):
    """Кастомное исключение для ошибок валидации кода."""
    pass


class CodeValidator:
    """Модуль статической валидации исходного кода через AST."""

    def validate_syntax(self, code: str) -> bool:
        """Проверяет синтаксическую валидность кода."""
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            raise CodeValidatorError(f"Syntax error: {e}")
        except Exception as e:
            raise CodeValidatorError(f"Error parsing syntax: {e}")

    def detect_empty_except(self, code: str) -> list:
        """Обнаруживает пустые блоки перехвата исключений (pass или ...)."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise CodeValidatorError(f"Syntax error during empty except detection: {e}")

        empty_excepts = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if len(node.body) == 1:
                    stmt = node.body[0]
                    is_pass = isinstance(stmt, ast.Pass)
                    is_ellipsis = isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant) and stmt.value.value == Ellipsis
                    if is_pass or is_ellipsis:
                        empty_excepts.append(node.lineno)
                elif not node.body:
                    empty_excepts.append(node.lineno)

        return empty_excepts

    def analyze_structure(self, code: str) -> dict:
        """Выполняет структурный анализ кода (подсчет классов и функций верхнего уровня)."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise CodeValidatorError(f"Invalid code structure: {e}")

        classes = []
        functions = []

        for node in tree.body:
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node.name)

        return {
            "classes": classes,
            "functions": functions
        }

    def validate_code(self, code: str) -> dict:
        """Возвращает полный отчет валидации кода."""
        is_valid = True
        try:
            self.validate_syntax(code)
        except CodeValidatorError:
            is_valid = False

        empty_excepts = []
        structure = {"classes": [], "functions": []}

        if is_valid:
            empty_excepts = self.detect_empty_except(code)
            structure = self.analyze_structure(code)

        return {
            "is_valid": is_valid,
            "empty_excepts": empty_excepts,
            "structure": structure
        }

    def validate(self, code: str) -> dict:
        """Интеграционный метод проверки кода (совместим с интеграционными тестами)."""
        syntax_valid = True
        try:
            self.validate_syntax(code)
        except CodeValidatorError:
            syntax_valid = False

        empty_except_blocks = []
        if syntax_valid:
            empty_except_blocks = self.detect_empty_except(code)

        return {
            "syntax_valid": syntax_valid,
            "empty_except_blocks": empty_except_blocks
        }

    def validate_file(self, file_path: str) -> dict:
        """Читает и валидирует файл по указанному пути."""
        if not os.path.exists(file_path):
            raise CodeValidatorError(f"File not found: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except IOError as e:
            raise CodeValidatorError(f"IO Error reading file {file_path}: {e}")

        return self.validate_code(content)