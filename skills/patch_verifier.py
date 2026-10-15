import ast
import os


class PatchVerifierError(Exception):
    """Исключение, выбрасываемое при ошибках верификации патча или кода."""
    pass


class PatchVerifier:
    """Модуль статической верификации патчей и сгенерированного кода."""

    def __init__(self, repo_path=None):
        self.repo_path = repo_path

    def verify_syntax(self, code_str: str) -> bool:
        """Проверяет синтаксис переданного кода с помощью AST."""
        try:
            ast.parse(code_str)
            return True
        except SyntaxError as e:
            raise PatchVerifierError(f"Синтаксическая ошибка: {e}")

    def verify_security_constraints(self, code_str: str) -> None:
        """Проверяет код на наличие запрещенных импортов и опасных функций."""
        forbidden_modules = {"os", "sys", "subprocess", "shutil", "eval", "exec"}
        forbidden_builtins = {"eval", "exec", "compile", "__import__"}

        try:
            tree = ast.parse(code_str)
        except SyntaxError as e:
            raise PatchVerifierError(f"Синтаксическая ошибка при проверке безопасности: {e}")

        for node in ast.walk(tree):
            # Проверка импортов
            if isinstance(node, ast.Import):
                for alias in node.names:
                    base_name = alias.name.split('.')[0]
                    if base_name in forbidden_modules:
                        raise PatchVerifierError(f"Запрещенный модуль: {base_name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    base_name = node.module.split('.')[0]
                    if base_name in forbidden_modules:
                        raise PatchVerifierError(f"Запрещенный модуль: {base_name}")

            # Проверка вызовов опасных функций / встроенных средств
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in forbidden_builtins:
                        raise PatchVerifierError(f"Запрещенная встроенная функция: {node.func.id}")

    def verify_ast_complexity(self, code_str: str, max_nodes: int = 1500) -> None:
        """Проверяет сложность AST кода (количество узлов не должно превышать лимит)."""
        try:
            tree = ast.parse(code_str)
        except SyntaxError as e:
            raise PatchVerifierError(f"Синтаксическая ошибка при проверке сложности: {e}")

        node_count = sum(1 for _ in ast.walk(tree))
        if node_count > max_nodes:
            raise PatchVerifierError(f"Превышен лимит узлов AST: {node_count} > {max_nodes}")

    def verify_and_approve(self, file_path: str) -> bool:
        """Читает файл по пути, проверяет его синтаксис, безопасность и сложность."""
        full_path = file_path
        if self.repo_path and not os.path.isabs(file_path):
            full_path = os.path.join(self.repo_path, file_path)

        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
        except (FileNotFoundError, IOError) as e:
            raise PatchVerifierError(f"Ошибка чтения файла {full_path}: {e}")

        self.verify_syntax(content)
        self.verify_security_constraints(content)
        self.verify_ast_complexity(content)
        return True

    def verify(self, patch_data: dict) -> bool:
        """Интеграционный метод проверки словаря патча с полями file_path и content."""
        content = patch_data.get("content", "")
        try:
            self.verify_syntax(content)
            self.verify_security_constraints(content)
            self.verify_ast_complexity(content)
            return True
        except PatchVerifierError:
            return False