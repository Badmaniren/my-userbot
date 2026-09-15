import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.dependency_parser import parse_requirement, parse_requires_dist, DependencyParser, _normalize_requirement

class TestDependencyParser(unittest.TestCase):

    def setUp(self):
        self.random_pkg_name = f"pkg-{uuid.uuid4().hex[:8]}"
        self.random_version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.operators = ["==", ">=", "<=", ">", "<", "!=", "~="]
        self.random_operator = random.choice(self.operators)
        self.random_marker = f"python_version < '{random.randint(3, 4)}.{random.randint(0, 9)}'"

    def test_normalize_requirement_valid(self):
        req_str = f"{self.random_pkg_name} {self.random_operator} {self.random_version}; {self.random_marker}"
        res = _normalize_requirement(req_str)
        self.assertEqual(res["name"], self.random_pkg_name)
        self.assertEqual(res["operator"], self.random_operator)
        self.assertEqual(res["version"], self.random_version)
        self.assertIn(self.random_pkg_name, req_str)

    def test_parse_requirement_alias(self):
        req_str = f"{self.random_pkg_name} {self.random_operator} {self.random_version}"
        res = parse_requirement(req_str)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["name"], self.random_pkg_name)
        self.assertEqual(res["version"], self.random_version)

    def test_parse_requires_dist_alias(self):
        req_str = f"{self.random_pkg_name}"
        res = parse_requires_dist(req_str)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["name"], self.random_pkg_name)
        self.assertIsNone(res["version"])
        self.assertIsNone(res["operator"])

    def test_dependency_parser_class_parse(self):
        parser = DependencyParser()
        req_str = f"{self.random_pkg_name}{self.random_operator}{self.random_version}"
        res = parser.parse(req_str)
        self.assertIsInstance(res, dict)
        self.assertEqual(res["name"], self.random_pkg_name)
        self.assertEqual(res["version"], self.random_version)

    def test_dependency_parser_stream(self):
        parser = DependencyParser()
        pkg_names = [f"dep-{uuid.uuid4().hex[:6]}" for _ in range(3)]
        stream_content = f"# Comment line\n\n{pkg_names[0]}==1.0.0\n{pkg_names[1]}>=2.0.0\n# Another comment\n{pkg_names[2]}\n"
        stream = io.BytesIO(stream_content.encode('utf-8'))

        results = parser.parse_stream(stream)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]["name"], pkg_names[0])
        self.assertEqual(results[0]["version"], "1.0.0")
        self.assertEqual(results[1]["name"], pkg_names[1])
        self.assertEqual(results[1]["operator"], ">=")
        self.assertEqual(results[2]["name"], pkg_names[2])
        self.assertIsNone(results[2]["version"])

if __name__ == '__main__':
    unittest.main()