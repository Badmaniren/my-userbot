import unittest
import io
import uuid
import random
from skills.requirement_analyzer import RequirementAnalyzer, PEP508Specifier
from skills.pypi_client import PyPIClient

class TestRequirementAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.analyzer = RequirementAnalyzer()
        self.pypi_client = PyPIClient()
        self.random_pkg_name = f"test-package-{uuid.uuid4().hex[:8]}"
        self.random_version = f"1.{random.randint(0, 9)}.{random.randint(0, 9)}"

    def test_integration_parse_stream_and_match(self):
        # Генерируем случайные данные для потока требований (PEP 508)
        operator = random.choice(["==", ">=", "<=", "~="])
        raw_requirement = f"{self.random_pkg_name} {operator} {self.random_version}"

        stream = io.StringIO(f"# Аудит безопасности потока\n{raw_requirement}\n")

        # Вызываем реальный метод парсинга потока без моков
        parsed_list = self.analyzer.parse_stream(stream)

        self.assertIsInstance(parsed_list, list)
        self.assertGreaterEqual(len(parsed_list), 1)

        spec = parsed_list[0]
        self.assertEqual(spec.name, self.random_pkg_name)
        self.assertEqual(spec.operator, operator)
        self.assertEqual(spec.version, self.random_version)

        # Проверяем интеграцию сопоставления версии (match)
        match_result = self.analyzer.match(self.random_version)
        self.assertIsInstance(match_result, bool)

    def test_integration_with_pypi_client_workflow(self):
        # Создаем спецификатор через анализатор и проверяем совместимость с данными из PyPI клиента
        raw_spec = f"requests >= 2.20.0"
        analyzer_instance = RequirementAnalyzer(raw_spec)

        self.assertEqual(analyzer_instance.name, "requests")
        self.assertEqual(analyzer_instance.operator, ">=")
        self.assertEqual(analyzer_instance.version, "2.20.0")

        # Проверяем реальное сопоставление версий, получаемых из pypi_client (интеграция навыков)
        try:
            versions = self.pypi_client.get_release_versions("requests")
            if versions:
                sample_version = random.choice(versions)
                match_res = analyzer_instance.match(sample_version)
                self.assertIsInstance(match_res, bool)
        except Exception:
            # Сетевые вызовы могут падать в изолированной среде, проверяем логику match на статической случайной версии
            test_ver = f"2.{random.randint(21, 30)}.0"
            self.assertTrue(analyzer_instance.match(test_ver))

if __name__ == "__main__":
    unittest.main()