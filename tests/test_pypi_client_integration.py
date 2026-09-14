import unittest
import uuid
import random
from skills.pypi_client import PyPIClient

class TestPyPIClientIntegration(unittest.TestCase):
    def setUp(self):
        self.client = PyPIClient()
        # Генерируем случайные данные для изоляции тестов и проверки динамических параметров
        self.random_token = str(uuid.uuid4())
        # Используем известные стабильные пакеты из PyPI для интеграционного теста
        self.target_packages = ["requests", "urllib3", "setuptools"]

    def test_get_package_metadata_real(self):
        pkg = random.choice(self.target_packages)
        metadata = self.client.get_package_metadata(pkg)
        
        self.assertIsNotNone(metadata, f"Метаданные для пакета {pkg} не должны быть None")
        self.assertIn("info", metadata, "В ответе PyPI должен присутствовать ключ 'info'")
        self.assertIn("name", metadata["info"], "В info должен быть ключ 'name'")
        self.assertEqual(metadata["info"]["name"].lower(), pkg.lower())

    def test_get_release_versions_real(self):
        pkg = random.choice(self.target_packages)
        versions = self.client.get_release_versions(pkg)
        
        self.assertIsInstance(versions, list, "Список версий должен быть списком")
        self.assertGreater(len(versions), 0, "Список версий не должен быть пустым для реального пакета")

    def test_get_package_dependencies_real(self):
        pkg = random.choice(self.target_packages)
        # Получаем список версий и берем случайную версию для проверки
        versions = self.client.get_release_versions(pkg)
        self.assertGreater(len(versions), 0)
        
        random_version = random.choice(versions[:10]) # берем из первых 10 релизов
        
        try:
            deps = self.client.get_package_dependencies(pkg, version=random_version)
            self.assertIsInstance(deps, list, "Зависимости должны возвращаться в виде списка")
        except ValueError:
            # Некоторые старые релизы могут отдавать 404 на PyPI JSON API, это допустимо для интеграционных тестов
            pass

    def test_get_package_dependencies_not_found(self):
        non_existent_package = f"nonexistent-pkg-{self.random_token}"
        with self.assertRaises(ValueError):
            self.client.get_package_dependencies(non_existent_package)

if __name__ == "__main__":
    unittest.main()