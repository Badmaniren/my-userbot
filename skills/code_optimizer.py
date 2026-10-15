import os
import ast

class CodeOptimizerError(Exception):
    """Исключение для ошибок оптимизации кода."""
    pass

class UnusedImportVisitor(ast.NodeVisitor):
    def __init__(self):
        self.imports = {}  # name -> node
        self.used_names = set()

    def visit_Import(self, node):
        for alias in node.names:
            name = alias.asname or alias.name
            self.imports[name] = node
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            name = alias.asname or alias.name
            self.imports[name] = node
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)

class CodeOptimizer:
    def __init__(self, repo_path, patch_executor=None, git_inspector=None, lesson_parser=None):
        self.repo_path = repo_path
        self.git_inspector = git_inspector
        self.lesson_parser = lesson_parser
        self.patch_executor = patch_executor

    def _get_changed_files(self):
        changes = []
        if self.git_inspector and hasattr(self.git_inspector, "get_latest_changes"):
            raw_changes = self.git_inspector.get_latest_changes() or []
            if isinstance(raw_changes, list):
                changes = raw_changes
            elif isinstance(raw_changes, str):
                for line in raw_changes.splitlines():
                    if line.startswith("+++ b/"):
                        file_path = line[6:].strip()
                        if file_path.endswith(".py"):
                            changes.append(file_path)

        if not changes and os.path.exists(self.repo_path):
            for root, _, files in os.walk(self.repo_path):
                for file in files:
                    if file.endswith(".py"):
                        changes.append(os.path.join(root, file))
        return changes

    def analyze_unused_imports(self, file_path):
        full_path = file_path if os.path.isabs(file_path) else os.path.join(self.repo_path, file_path)
        if not os.path.isfile(full_path):
            return []
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            tree = ast.parse(content)
        except Exception:
            return []

        visitor = UnusedImportVisitor()
        visitor.visit(tree)

        unused = []
        for name, node in visitor.imports.items():
            if name not in visitor.used_names:
                for alias in node.names:
                    alias_name = alias.asname or alias.name
                    if alias_name == name:
                        if isinstance(node, ast.Import):
                            unused.append(f"import {alias.name}")
                        else:
                            unused.append(name)
        return unused

    def optimize_code(self):
        changes = self._get_changed_files()

        optimized_files = {}
        for file_path in changes:
            full_path = file_path if os.path.isabs(file_path) else os.path.join(self.repo_path, file_path)
            if not os.path.isfile(full_path):
                continue
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            except (OSError, IOError):
                continue

            try:
                tree = ast.parse("".join(lines))
            except SyntaxError:
                continue

            visitor = UnusedImportVisitor()
            visitor.visit(tree)

            unused = {name for name, node in visitor.imports.items() if name not in visitor.used_names}

            unused_import_lines = set()
            for node in tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    names = {alias.asname or alias.name for alias in node.names}
                    if names and names.issubset(unused):
                        if hasattr(node, "lineno") and hasattr(node, "end_lineno") and node.lineno and node.end_lineno:
                            for idx in range(node.lineno - 1, node.end_lineno):
                                unused_import_lines.add(idx)

            new_lines = [line for idx, line in enumerate(lines) if idx not in unused_import_lines]

            try:
                with open(full_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                optimized_files[file_path] = True
            except (OSError, IOError):
                continue

        return optimized_files

    def optimize_structure(self, metrics):
        for v in metrics.values():
            if isinstance(v, (int, float)) and v < 0:
                raise CodeOptimizerError("Negative metric value")
        if self.patch_executor:
            try:
                if hasattr(self.patch_executor, "apply_patch"):
                    return self.patch_executor.apply_patch(metrics)
            except Exception as e:
                raise CodeOptimizerError(str(e))
        return True

    def run_optimization_pipeline(self):
        try:
            self.optimize_code()
            results = {}
            if self.patch_executor and hasattr(self.patch_executor, "execute_from_lessons"):
                res = self.patch_executor.execute_from_lessons()
                if isinstance(res, dict):
                    results.update(res)
            return results if results else {"status": True}
        except Exception as e:
            raise CodeOptimizerError(str(e))
