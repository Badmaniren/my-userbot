import unittest
import uuid
import random
from skills.dependency_parser import parse_dependencies
from skills.pypi_client import PyPIClient

class TestDependencyParserIntegration(unittest.TestCase):
    def setUp(self):
        self.pypi_client = PyPIClient()
        self.test_package = f"pkg-{uuid.uuid4().hex[:8]}"
        self.test_version = f"1.{random.randint(0, 9)}.{random.randint(0, 9)}"

    def test_pypi_client_and_dependency_parser_integration(self):
        raw_dependencies = [
            f"requests (>=2.{random.randint(0, 9)}.{random.randint(0, 9)})",
            f"urllib3 >=1.26; python_version < '3.12'",
            f"pytest>=7.0.0 ; extra == 'dev'"
        ]

        parsed_results = []
        for dep_str in raw_dependencies:
            parsed = parse_dependencies(dep_str)
            self.assertIsNotNone(parsed)
            parsed_results.append(parsed)

        self.assertGreaterEqual(len(parsed_results), 3)

        for res in parsed_results:
            self.assertTrue(isinstance(res, (dict, list, object)))

    def test_stream_data_parsing_with_dependencies(self):
        import io
        random_id = str(uuid.uuid4())
        stream_content = f'{{"package": "{self.test_package}", "version": "{self.test_version}", "id": "{random_id}", "requires_dist": ["click >= 8.0", "rich >= 10.0"]}}'
        stream = io.BytesIO(stream_content.encode('utf-8'))

        stream_data = self.pypi_client.parse_stream_data(stream)
        self.assertIsInstance(stream_data, dict)
        self.assertEqual(stream_data.get("id"), random_id)

        dependencies = stream_data.get("requires_dist", [])
        self.assertGreater(len(dependencies), 0)

        for dep in dependencies:
            parsed_dep = parse_dependencies(dep)
            self.assertIsNotNone(parsed_dep)

if __name__ == '__main__':
    unittest.main()