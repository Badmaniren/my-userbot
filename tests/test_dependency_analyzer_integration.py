import unittest
import uuid
import random
import tempfile
import shutil
from pathlib import Path

from skills.dependency_analyzer import DependencyAnalyzer
from skills.git_inspector import GitInspector


class TestDependencyAnalyzerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        # Инициализация реального репозитория через GitInspector (или прямое создание структуры)
        # Так как нам нужны реальные файлы для анализа зависимостей, создадим их на диске
        self.random_module_name = f"module_{uuid.uuid4().hex[:8]}"
        self.random_dependency_name = f"dep_{uuid.uuid4().hex[:8]}"

        # Создаем файлы с импортами друг друга для проверки статичного анализа
        dep_file = Path(self.repo_path) / f"{self.random_dependency_name}.py"
        dep_file.write_text(f"# {random.randint(1000, 9999)}\nclass {self.random_dependency_name.capitalize()}:\n    pass\n", encoding="utf-8")

        main_file = Path(self.repo_path) / f"{self.random_module_name}.py"
        main_file.write_text(
            f"import {self.random_dependency_name}\n\n"
            f"def run_{uuid.uuid4().hex[:4]}():\n"
            f"    return {self.random_dependency_name}.{self.random_dependency_name.capitalize()}()\n",
            encoding="utf-8"
        )

        self.git_inspector = GitInspector(repo_path=self.repo_path)
        self.dependency_analyzer = DependencyAnalyzer(repo_path=self.repo_path, git_inspector=self.git_inspector)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_dependency_analyzer_integration(self):
        # Вызов реального метода анализа без моков
        dependency_map = self.dependency_analyzer.analyze_dependencies()

        # Проверяем, что карта связей возвращает словарь и содержит созданные динамически модули
        self.assertIsInstance(dependency_map, dict)

        # Проверяем наличие случайно сгенерированных сущностей в результатах анализа
        found_modules = list(dependency_map.keys())
        self.assertTrue(
            any(self.random_module_name in mod for mod in found_modules),
            f"Модуль {self.random_module_name} не найден в карте зависимостей: {found_modules}"
        )

        # Проверка поиска устаревшего кода / неиспользуемых зависимостей
        unused_code = self.dependency_analyzer.find_unused_code()
        self.assertIsInstance(unused_code, (list, set, dict))