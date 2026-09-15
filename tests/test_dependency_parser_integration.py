import unittest
import uuid
import random
from skills.dependency_parser import parse_dependency_string
from skills.pypi_client import PyPIClient

class TestDependencyParserIntegration(unittest.TestCase):
    def setUp(self):
        self.random_string_id = str(uuid.uuid4())
        self.client = PyPIClient()

    def test_dependency_parser_integration_with_pypi(self):
        package_name = f"requests-{self.random_string_id[:6]}"
        raw_requires_dist = [
            f"urllib3 (>=1.21.1,<1.27)",
            f"idna (<3,>=2.5)",
            f"certifi (>=2017.4.17)"
        ]
        
        parsed_results = []
        for req in raw_requires_dist:
            parsed = parse_dependency_string(req)
            if parsed:
                parsed_results.append(parsed)

        self.assertGreaterEqual(len(parsed_results), 1)
        
        for item in parsed_results:
            self.assertIn("name", item)
            self.assertIn("version_constraint", item)

    def test_randomized_dependency_parsing(self):
        versions = [f"1.{random.randint(0, 9)}.{random.randint(0, 9)}" for _ in range(3)]
        test_cases = [
            f"numpy (>={versions[0]})",
            f"pandas (>={versions[1]},<2.0.0)",
            f"scipy =={versions[2]}"
        ]
        
        selected_case = random.choice(test_cases)
        result = parse_dependency_string(selected_case)
        
        self.assertIsInstance(result, dict)
        self.assertIn("name", result)
        self.assertTrue(len(result["name"]) > 0)

if __name__ == "__main__":
    unittest.main()