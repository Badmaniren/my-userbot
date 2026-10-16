import ast
import os
import textwrap
from typing import Dict, Any, List, Union

from skills.code_sanitizer import CodeSanitizer, CodeAntipatternDetectedError


class CodeValidatorError(Exception):
    """Базовое исключение для ошибок валидации кода."""
    pass


class ASTValidationError(CodeValidatorError):
    """Исключение для ошибок AST валидации."""
    pass


class ASTReport(dict):
    """Словарь с поддержкой булева приведения для совместимости с тестами."""
    def __bool__(self):
        return self.get("is_valid", False)


class CodeValidator:
    """Модуль статической валидации и проверки AST структуры кода."""

    def __init__(
        self,
        repo_path: str = ".",
        forbidden_nodes: Union[List[str], None] = None,
        max_complexity: int = 20,
    ):
        self.repo_path = repo_path
        self.forbidden_nodes = ["eval", "exec", "__import__", "system", "os", "subprocess", "popen"]
        if forbidden_nodes:
            for node in forbidden_nodes:
                if node not in self.forbidden_nodes:
                    self.forbidden_nodes.append(node)
        self.max_complexity = max_complexity

    def add_forbidden_rule(self, rule: str) -> None:
        """Динамическое добавление правила запрета."""
        if rule not in self.forbidden_nodes:
            self.forbidden_nodes.append(rule)

    def validate_syntax(self, code: str) -> bool:
        """Проверка синтаксиса Python кода."""
        try:
            ast.parse(code)
            return True
        except SyntaxError as e:
            raise ASTValidationError(f"Syntax error: {e}")

    def check_complexity(self, code: str) -> int:
        """Оценка цикломатической сложности кода через подсчет ветвлений в AST."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return 1

        complexity = 1
        for node in ast.walk(tree):
            if isinstance(
                node,
                (
                    ast.If,
                    ast.While,
                    ast.For,
                    ast.AsyncFor,
                    ast.ExceptHandler,
                    ast.With,
                    ast.AsyncWith,
                    ast.Assert,
                    ast.comprehension,
                ),
            ):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                complexity += len(node.values) - 1
        return complexity

    def validate_ast(self, code: str) -> Union[bool, Dict[str, Any]]:
        """Проверка AST на запрещенные узлы, вызовы и сложность."""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return ASTReport({
                "is_valid": False,
                "violations": [f"Syntax error: {e}"],
                "complexity": 1,
                "error": str(e),
            })

        violations = []

        # Проверка сложности
        complexity = self.check_complexity(code)
        if complexity > self.max_complexity:
            violations.append(
                f"Complexity {complexity} exceeds max_complexity {self.max_complexity}"
            )

        # Проверка запрещенных нод/функций
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = ""
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in self.forbidden_nodes:
                    violations.append(f"Forbidden function call: {func_name}")

            elif isinstance(node, ast.Name):
                if node.id in self.forbidden_nodes:
                    violations.append(f"Forbidden name reference: {node.id}")

        is_valid = len(violations) == 0

        return ASTReport({
            "is_valid": is_valid,
            "violations": violations,
            "complexity": complexity,
        })

    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """Валидация файла по указанному пути."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except (FileNotFoundError, OSError) as e:
            raise FileNotFoundError(f"File not found: {file_path}") from e

        ast_report = self.validate_ast(content)
        is_valid = bool(ast_report["is_valid"])
        res = {
            "is_valid": is_valid,
            "file_path": file_path,
            "violations": ast_report.get("violations", []),
            "status": "success" if is_valid else "failed",
        }
        if "error" in ast_report:
            res["error"] = ast_report["error"]
        return res

    def validate_patch(self, patch_diff: str) -> Dict[str, Any]:
        """Валидация патча (diff) путем извлечения добавленного кода."""
        added_lines = []
        for line in patch_diff.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                added_lines.append(line[1:])

        code_to_check = textwrap.dedent("\n".join(added_lines))
        ast_report = self.validate_ast(code_to_check)
        return {
            "is_valid": bool(ast_report["is_valid"]),
            "violations": ast_report.get("violations", []),
        }

    def batch_validate(self, items: Dict[str, str]) -> Dict[str, Dict[str, Any]]:
        """Пакетная валидация словаря с кодом."""
        results = {}
        for key, code in items.items():
            report = self.validate_ast(code)
            results[key] = {
                "is_valid": bool(report["is_valid"]),
                "violations": report.get("violations", []),
            }
        return results

    def validate_stream(self, stream: Any) -> Dict[str, Any]:
        """Валидация кода из потока (stream)."""
        content = stream.read().decode("utf-8")
        report = self.validate_ast(content)
        return {
            "is_valid": bool(report["is_valid"]),
            "violations": report.get("violations", []),
        }
