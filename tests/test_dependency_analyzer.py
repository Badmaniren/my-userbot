import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import os
import ast

from skills.dependency_analyzer import DependencyAnalyzer, DependencyAnalyzerError


class TestDependencyAnalyzer(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.analyzer = DependencyAnalyzer(repo_path=self.repo_path)
        self.random_module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.random_imported_module = f"module_{uuid.uuid4().hex[:8]}"
        self.random_func_name = f"func_{uuid.uuid4().hex[:8]}"

    def test_initialization_validates_path(self):
        self.assertEqual(self.analyzer.repo_path, self.repo_path)
        self.assertIsInstance(self.analyzer, DependencyAnalyzer)

    def test_extract_imports_success(self):
        random_code = f"import {self.random_imported_module}\nfrom module_{uuid.uuid4().hex} import {self.random_func_name}"

        with patch('os.walk') as mock_walk, \
             patch('builtins.open', unittest.mock.mock_open(read_data=random_code)):

            mock_walk.return_value = [
                (self.repo_path, (), [f"{self.random_module_name}.py"])
            ]

            imports = self.analyzer.extract_imports()

            self.assertIn(self.random_imported_module, imports.get(f"{self.random_module_name}.py", []))

    def test_extract_imports_handles_syntax_error(self):
        corrupted_code = f"import {uuid.uuid4().hex} \n def {uuid.uuid4().hex}(: syntax error"

        with patch('os.walk') as mock_walk, \
             patch('builtins.open', unittest.mock.mock_open(read_data=corrupted_code)):

            mock_walk.return_value = [
                (self.repo_path, (), [f"{self.random_module_name}.py"])
            ]

            # Должно корректно обрабатывать ошибки синтаксиса без падения всего анализа
            imports = self.analyzer.extract_imports()
            self.assertIn(f"{self.random_module_name}.py", imports)
            self.assertEqual(imports[f"{self.random_module_name}.py"], [])

    def test_build_dependency_map(self):
        mod_a = f"mod_{uuid.uuid4().hex[:6]}.py"
        mod_b = f"mod_{uuid.uuid4().hex[:6]}"

        mock_imports_data = {
            mod_a: [mod_b],
            f"{mod_b}.py": []
        }

        with patch.object(self.analyzer, 'extract_imports', return_value=mock_imports_data):
            dep_map = self.analyzer.build_dependency_map()

            self.assertIn(mod_a, dep_map)
            self.assertIn(mod_b, dep_map[mod_a])

    def test_find_unused_modules(self):
        active_mod = f"active_{uuid.uuid4().hex[:6]}.py"
        dead_mod = f"dead_{uuid.uuid4().hex[:6]}.py"

        dep_map = {
            active_mod: [],
            dead_mod: []
        }

        # active_mod упомянут в зависимостях другого модуля, dead_mod - нет
        other_mod = f"other_{uuid.uuid4().hex[:6]}.py"
        full_dep_map = {
            other_mod: [active_mod.replace('.py', '')],
            active_mod: [],
            dead_mod: []
        }

        with patch.object(self.analyzer, 'build_dependency_map', return_value=full_dep_map):
            unused = self.analyzer.find_unused_modules()

            self.assertIn(dead_mod, unused)
            self.assertNotIn(active_mod, unused)

    def test_analyze_raises_custom_exception_on_io_failure(self):
        with patch('os.walk', side_effect=OSError(f"Disk error {uuid.uuid4().hex}")):
            with self.assertRaises(DependencyAnalyzerError):
                self.analyzer.extract_imports()

    def test_read_file_safe_stream(self):
        random_content = f"content_{uuid.uuid4().hex}".encode('utf-8')
        mock_file = io.BytesIO(random_content)

        with patch('builtins.open', return_value=mock_file):
            result = self.analyzer._read_file_content(f"/{uuid.uuid4().hex}.py")
            self.assertIn(random_content.decode('utf-8'), result)


if __name__ == '__main__':
    unittest.main()