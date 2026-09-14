import unittest
import io
import uuid
import random
from skills.dependency_parser import DependencyParser, parse_dependency_string
from skills.pypi_client import PyPIClient

class TestDependencyParserIntegration(unittest.TestCase):
    def setUp(self):
        self.parser = DependencyParser()
        self.pypi_client = PyPIClient()
        self.test_package = "requests"
        self.test_version = "2.31.0"
        self.random_tag = str(uuid.uuid4())[:8]

    def test_parse_single_dependency_real_flow(self):
        random_version_num = f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        dep_str = f"urllib3>={random_version_num}; python_version < '3.12'"

        result = self.parser.parse(dep_str)

        self.assertEqual(result["name"], "urllib3")
        self.assertIn(random_version_num, result["version_constraint"])
        self.assertIsNotNone(result["marker"])

    def test_parse_stream_integration_with_pypi(self):
        deps = self.pypi_client.get_dependencies(self.test_package, self.test_version)

        if not deps:
            deps = [f"charset-normalizer<3.0,>=2.0 ; python_version >= '{self.random_tag}'"]

        stream_content = "\n".join(deps)
        stream = io.StringIO(stream_content)

        parsed_results = self.parser.parse_stream(stream)

        self.assertIsInstance(parsed_results, list)
        if parsed_results:
            first_dep = parsed_results[0]
            self.assertIn("name", first_dep)
            self.assertIn("version_constraint", first_dep)

    def test_parse_batch_randomized_data(self):
        package_names = ["certifi", "idna", "urllib3", f"pkg-{self.random_tag}"]
        dep_strings = [f"{pkg}=={random.randint(1, 3)}.0.0" for pkg in package_names]

        batch_results = self.parser.parse_batch(dep_strings)

        self.assertEqual(len(batch_results), len(dep_strings))
        for i, res in enumerate(batch_results):
            self.assertEqual(res["name"], package_names[i])
            self.assertIsNotNone(res["version"])

    def test_convenience_function_error_handling(self):
        invalid_str = f"invalid-dep-syntax-!@#-{self.random_tag}"

        with self.assertRaises(ValueError):
            parse_dependency_string(invalid_str)

if __name__ == "__main__":
    unittest.main()