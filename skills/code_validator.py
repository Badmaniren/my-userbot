import ast
import io
from typing import Dict, Any, Union, Set


class CodeValidatorError(Exception):
    """Базовое исключение валидатора кода."""
    pass


class CodeValidatorASTError(CodeValidatorError):
    """Ошибка синтаксиса или структуры AST."""
    pass


class CodeValidatorAntipatternError(CodeValidatorError):
    """Обнаружен запрещенный антипаттерн в коде."""
    pass


class AntipatternVisitor(ast.NodeVisitor):
    """AST визитор для поиска запрещенных конструкций и антипаттернов."""
    
    def __init__(self, forbidden_constructs: Set[str]):
        self.forbidden_constructs = forbidden_constructs

    def visit_Name(self, node: ast.Name):
        if node.id in self.forbidden_constructs:
            raise CodeValidatorAntipatternError(f"Обнаружен запрещенный конструкт: {node.id}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            if node.func.id in self.forbidden_constructs:
                raise CodeValidatorAntipatternError(f"Обнаружен вызов запрещенного конструкта: {node.func.id}")
        elif isinstance(node.func, ast.Attribute):
            if node.func.attr in self.forbidden_constructs:
                raise CodeValidatorAntipatternError(f"Обнаружен вызов запрещенного атрибута: {node.func.attr}")
        self.generic_visit(node)


class CodeValidator:
    """Модуль для семантической валидации санитизированного кода патчей."""

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.forbidden_constructs: Set[str] = set()

    def add_forbidden_construct(self, construct: str) -> None:
        self.forbidden_constructs.add(construct)

    def _check_ast(self, tree: ast.AST) -> bool:
        visitor = AntipatternVisitor(self.forbidden_constructs)
        visitor.visit(tree)
        return True

    def validate_code(self, code: str) -> bool:
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            raise CodeValidatorASTError(f"Ошибка синтаксиса AST: {e}") from e
        return self._check_ast(tree)

    def validate_patch_ast(self, code: str) -> bool:
        return self.validate_code(code)

    def validate_stream(self, stream: Union[io.IOBase, str]) -> bool:
        if isinstance(stream, str):
            content = stream
        else:
            content = stream.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8')
        return self.validate_code(content)

    def batch_validate(self, patches: Union[Dict[str, str], Dict[str, Any]]) -> Dict[str, Any]:
        if "patches" in patches and isinstance(patches["patches"], list):
            batch_id = patches.get("batch_id", "")
            results = []
            for patch_code in patches["patches"]:
                try:
                    is_valid = self.validate_code(patch_code)
                    results.append({"is_valid": is_valid})
                except CodeValidatorError:
                    results.append({"is_valid": False})
            return {
                "batch_id": batch_id,
                "results": results
            }
        
        passed = []
        failed = []
        results = {}
        for patch_id, patch_code in patches.items():
            try:
                is_valid = self.validate_code(patch_code)
                if is_valid:
                    passed.append(patch_id)
                    results[patch_id] = True
                else:
                    failed.append(patch_id)
                    results[patch_id] = False
            except CodeValidatorError:
                failed.append(patch_id)
                results[patch_id] = False
                
        results["passed"] = passed
        results["failed"] = failed
        return results