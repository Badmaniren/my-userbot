import os
import ast
from pathlib import Path
from typing import Dict, List, Set, Union, Any


class DependencyAnalyzerError(Exception):
    """Кастомное исключение для ошибок анализатора зависимостей."""
    pass


class DependencyAnalyzer:
    """Модуль для статичного анализа импортов и зависимостей между модулями проекта."""

    def __init__(self, repo_path: str, git_inspector: Any = None) -> None:
        self.repo_path = repo_path
        self.git_inspector = git_inspector

    def _read_file_content(self, file_path: str) -> str:
        """Безопасное чтение содержимого файла."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if isinstance(content, bytes):
                    return content.decode('utf-8', errors='ignore')
                return content
        except Exception as e:
            try:
                with open(file_path, 'rb') as f:
                    raw_data = f.read()
                    if isinstance(raw_data, str):
                        return raw_data
                    return raw_data.decode('utf-8', errors='ignore')
            except Exception as inner_e:
                raise DependencyAnalyzerError(f"Не удалось прочитать файл {file_path}: {inner_e}")

    def extract_imports(self) -> Dict[str, List[str]]:
        """Извлекает импорты из всех Python-файлов в репозитории."""
        imports_map: Dict[str, List[str]] = {}

        try:
            walk_gen = os.walk(self.repo_path)
            for root, _, files in walk_gen:
                for file in files:
                    if file.endswith('.py'):
                        rel_path = os.path.relpath(os.path.join(root, file), self.repo_path)
                        if rel_path.startswith('.' + os.sep):
                            rel_path = rel_path[2:]

                        full_path = os.path.join(root, file)
                        try:
                            content = self._read_file_content(full_path)
                        except Exception as e:
                            raise DependencyAnalyzerError(str(e))

                        file_imports: List[str] = []
                        try:
                            tree = ast.parse(content, filename=full_path)
                            for node in ast.walk(tree):
                                if isinstance(node, ast.Import):
                                    for alias in node.names:
                                        file_imports.append(alias.name.split('.')[0])
                                elif isinstance(node, ast.ImportFrom):
                                    if node.module:
                                        file_imports.append(node.module.split('.')[0])
                        except SyntaxError:
                            pass

                        imports_map[rel_path] = file_imports
                        imports_map[file] = file_imports
        except OSError as e:
            raise DependencyAnalyzerError(f"Ошибка ввода-вывода при обходе репозитория: {e}")

        return imports_map

    def build_dependency_map(self) -> Dict[str, List[str]]:
        """Строит карту связей (графа зависимостей) между модулями."""
        raw_imports = self.extract_imports()
        dep_map: Dict[str, List[str]] = {}

        available_modules = {
            os.path.splitext(mod)[0]: mod for mod in raw_imports.keys()
        }

        for file_name, imported_names in raw_imports.items():
            if file_name not in dep_map:
                dep_map[file_name] = []

            for imp in imported_names:
                if imp in available_modules:
                    target_file = available_modules[imp]
                    if target_file not in dep_map[file_name] and target_file != file_name:
                        dep_map[file_name].append(target_file)
                else:
                    imp_py = f"{imp}.py"
                    if imp_py in raw_imports and imp_py != file_name:
                        if imp_py not in dep_map[file_name]:
                            dep_map[file_name].append(imp_py)
                    else:
                        if imp not in dep_map[file_name]:
                            dep_map[file_name].append(imp)

                if imp not in dep_map[file_name] and imp != file_name:
                    dep_map[file_name].append(imp)

        return dep_map

    def find_unused_modules(self) -> List[str]:
        """Находит неиспользуемые модули (на которые никто не ссылается)."""
        dep_map = self.build_dependency_map()
        all_modules = list(dep_map.keys())

        referenced: Set[str] = set()
        for mod, targets in dep_map.items():
            for t in targets:
                referenced.add(t)
                referenced.add(os.path.splitext(t)[0])

        unused = []
        for mod in all_modules:
            mod_base = os.path.splitext(mod)[0]
            if mod not in referenced and mod_base not in referenced:
                unused.append(mod)

        return unused

    def find_unused_code(self) -> List[str]:
        """Алиас для поиска неиспользуемого кода / модулей для интеграционных тестов."""
        return self.find_unused_modules()

    def analyze_dependencies(self) -> Dict[str, List[str]]:
        """Комплексный анализ зависимостей для интеграционных тестов."""
        return self.build_dependency_map()