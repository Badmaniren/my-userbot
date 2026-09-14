import ast
import io

def sandbox_exec(code: str):
    """
    Заглушка безопасного песочного выполнения для динамического анализа.
    В реальной среде здесь может быть изолированный процесс/окружение.
    """
    try:
        local_vars = {}
        exec(code, {}, local_vars)
        if "execute_patch" in local_vars:
            res = local_vars["execute_patch"]()
            return True, res, ""
        return True, None, ""
    except Exception as e:
        return False, None, str(e)


class PatchValidator:
    """
    Модуль статического и динамического анализа сгенерированных патчей
    для безопасной верификации перед применением в error_recovery_hub.
    """
    def __init__(self):
        self.forbidden_modules = {"os", "sys", "subprocess", "shutil", "eval", "exec"}

    def analyze_static(self, code_str: str) -> dict:
        try:
            tree = ast.parse(code_str)
        except SyntaxError as e:
            return {"is_valid": False, "error": f"SyntaxError: {e}"}

        class ASTInspector(ast.NodeVisitor):
            def __init__(self, forbidden):
                self.forbidden = forbidden
                self.error = None

            def visit_Import(self, node):
                for alias in node.names:
                    base_name = alias.name.split('.')[0]
                    if base_name in self.forbidden:
                        self.error = f"Forbidden import: {base_name}"
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                if node.module:
                    base_name = node.module.split('.')[0]
                    if base_name in self.forbidden:
                        self.error = f"Forbidden import: {base_name}"
                self.generic_visit(node)

            def visit_Call(self, node):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.forbidden:
                        self.error = f"Forbidden call: {node.func.id}"
                self.generic_visit(node)

        inspector = ASTInspector(self.forbidden_modules)
        inspector.visit(tree)

        if inspector.error:
            return {"is_valid": False, "error": inspector.error}

        return {"is_valid": True, "error": None}

    def analyze_dynamic(self, code_str: str) -> dict:
        success, res, err = sandbox_exec(code_str)
        if success:
            return {"executed": True, "result": res}
        else:
            return {"executed": False, "error": err}

    def verify_patch(self, code_str: str) -> dict:
        static_res = self.analyze_static(code_str)
        if not static_res.get("is_valid"):
            return {
                "passed": False,
                "static_passed": False,
                "dynamic_passed": False
            }

        dynamic_res = self.analyze_dynamic(code_str)
        dynamic_passed = dynamic_res.get("executed", False)

        passed = bool(static_res.get("is_valid")) and dynamic_passed
        return {
            "valid": passed,
            "passed": passed,
            "static_passed": bool(static_res.get("is_valid")),
            "dynamic_passed": dynamic_passed
        }

    def verify_stream(self, stream) -> dict:
        if hasattr(stream, "read"):
            raw = stream.read()
            if isinstance(raw, bytes):
                code_str = raw.decode('utf-8')
            else:
                code_str = str(raw)
        elif isinstance(stream, bytes):
            code_str = stream.decode('utf-8')
        else:
            code_str = str(stream)
        return self.verify_patch(code_str)

    def validate(self, patch_data) -> bool:
        if isinstance(patch_data, str):
            res = self.verify_patch(patch_data)
            return res.get("passed", False)
        elif isinstance(patch_data, dict):
            code = patch_data.get("code", "")
            res = self.verify_patch(code)
            return res.get("passed", False)
        return False