import unittest
import io
import uuid
import random
from skills.dependency_parser import DependencyParser, parse_requires_dist, parse_dependencies
from skills.pypi_client import PyPIClient

class TestDependencyParserIntegration(unittest.TestCase):
    def setUp(self):
        self.parser = DependencyParser()
        self.random_suffix = str(uuid.uuid4())[:8]
        self.package_name = f"test-pkg-{self.random_suffix}"
        self.version = f"1.{random.randint(0, 9)}.{random.randint(0, 9)}"

    def test_integration_with_pypi_client_flow(self):
        client = PyPIClient()
        raw_deps = [
            f"requests (>=2.28.0); python_version < '3.12'",
            f"click (>=8.0) ; extra == 'cli'",
            f"pydantic[email] (>=2.0)"
        ]

        stream_data = "\n".join(raw_deps).encode('utf-8')
        stream = io.BytesIO(stream_data)

        parsed_stream_items = self.parser.parse_stream(stream)

        self.assertIsInstance(parsed_stream_items, list)
        self.assertEqual(len(parsed_stream_items), 3)

        self.assertEqual(parsed_stream_items[0]["name"], "requests")
        self.assertEqual(parsed_stream_items[0]["specifiers"], ">=2.28.0")
        self.assertIn("python_version", parsed_stream_items[0]["marker"])

        self.assertEqual(parsed_stream_items[1]["name"], "click")
        self.assertIn("cli", parsed_stream_items[1]["extras"])

        self.assertEqual(parsed_stream_items[2]["name"], "pydantic")
        self.assertIn("email", parsed_stream_items[2]["extras"])

    def test_dependency_graph_building_with_randomized_input(self):
        dep_1 = f"pkg-alpha-{self.random_suffix} (==1.0.0)"
        dep_2 = f"pkg-beta-{self.random_suffix} (>=2.5.1)"

        dep_list = [dep_1, dep_2]
        graph = self.parser.build_graph(dep_list)

        self.assertIsInstance(graph, dict)
        self.assertIn(f"pkg-alpha-{self.random_suffix}", graph)
        self.assertIn(f"pkg-beta-{self.random_suffix}", graph)

        alpha_node = graph[f"pkg-alpha-{self.random_suffix}"]
        self.assertEqual(alpha_node["specifiers"], "==1.0.0")

    def test_convenience_functions_integration(self):
        single_req = f"fastapi (>=0.100.0); extra == '{self.random_suffix}'"
        parsed_single = parse_requires_dist(single_req)

        self.assertEqual(parsed_single["name"], "fastapi")
        self.assertEqual(parsed_single["specifiers"], ">=0.100.0")
        self.assertIn(self.random_suffix, parsed_single["marker"])

        multi_reqs = [
            "uvicorn (>=0.20.0)",
            "sqlalchemy (>=2.0.0)"
        ]
        parsed_multi = parse_dependencies(multi_reqs)
        self.assertEqual(len(parsed_multi), 2)
        self.assertEqual(parsed_multi[0]["name"], "uvicorn")
        self.assertEqual(parsed_multi[1]["name"], "sqlalchemy")

if __name__ == '__main__':
    unittest.main()