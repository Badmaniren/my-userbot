import unittest
import io
import random
import uuid
from skills.dependency_parser import DependencyParser, parse_requirement, parse_requires_dist

class TestDependencyParserIntegration(unittest.TestCase):
    def setUp(self):
        self.parser = DependencyParser()
        self.rand_str = str(uuid.uuid4())[:8]
        self.test_package_name = f"pkg-{self.rand_str}"
        self.test_version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"

    def test_parse_single_requirement_real_data(self):
        req_line = f"{self.test_package_name} >= {self.test_version}; python_version < '3.12'"

        result_func = parse_requirement(req_line)
        result_class = self.parser.parse(req_line)
        result_alias = parse_requires_dist(req_line)

        self.assertEqual(result_func["name"], self.test_package_name.lower())
        self.assertEqual(result_func["operator"], ">=")
        self.assertEqual(result_func["version"], self.test_version)
        self.assertIn("python_version", result_func["environment_marker"])

        self.assertEqual(result_class, result_func)
        self.assertEqual(result_alias, result_func)

    def test_parse_stream_real_data(self):
        other_pkg = f"dep-{str(uuid.uuid4())[:6]}"
        stream_content = f"# Comment line\n\n{self.test_package_name}=={self.test_version}\n{other_pkg}>=1.0.0; extra == 'dev'\n"
        stream = io.BytesIO(stream_content.encode('utf-8'))

        results = self.parser.parse_stream(stream)

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)

        self.assertEqual(results[0]["name"], self.test_package_name.lower())
        self.assertEqual(results[0]["operator"], "==")
        self.assertEqual(results[0]["version"], self.test_version)

        self.assertEqual(results[1]["name"], other_pkg.lower())
        self.assertEqual(results[1]["operator"], ">=")
        self.assertEqual(results[1]["version"], "1.0.0")
        self.assertTrue(len(results[1]["markers"]) > 0)

if __name__ == "__main__":
    unittest.main()