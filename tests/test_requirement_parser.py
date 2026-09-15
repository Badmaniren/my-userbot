import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.requirement_parser import RequirementParser, parse_requirements

class TestRequirementParser(unittest.TestCase):

    def setUp(self):
        self.parser = RequirementParser()
        self.random_pkg_name = f"pkg-{uuid.uuid4().hex[:8]}"
        self.random_version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.random_extra = ''.join(random.choices(string.ascii_lowercase, k=6))

    def test_parse_valid_requirement(self):
        req_str = f"{self.random_pkg_name}=={self.random_version}"
        result = self.parser.parse(req_str)
        self.assertEqual(result["name"], self.random_pkg_name)
        self.assertIn(f"=={self.random_version}", result["specs"])
        self.assertEqual(result["version"], self.random_version)
        self.assertIsNone(result["marker"])
        self.assertEqual(result["extras"], [])

    def test_parse_with_extras_and_marker(self):
        random_env = ''.join(random.choices(string.ascii_lowercase, k=5))
        req_str = f"{self.random_pkg_name}[{self.random_extra}]>={self.random_version}; python_version < '{random_env}'"
        result = self.parser.parse(req_str)
        self.assertEqual(result["name"], self.random_pkg_name)
        self.assertIn(self.random_extra, result["extras"])
        self.assertEqual(result["version"], self.random_version)
        self.assertIsNotNone(result["marker"])

    def test_parse_invalid_requirement(self):
        invalid_str = f"===!invalid@@@name{uuid.uuid4().hex}"
        with self.assertRaises(Exception) as ctx:
            self.parser.parse(invalid_str)
        self.assertIn("Invalid requirement", str(ctx.exception))

    def test_parse_line_alias(self):
        req_str = f"{self.random_pkg_name}~={self.random_version}"
        result = self.parser.parse_line(req_str)
        self.assertEqual(result["name"], self.random_pkg_name)
        self.assertIsNotNone(result["specs"])

    def test_parse_stream(self):
        comment_line = f"# {uuid.uuid4().hex}"
        pkg_line_1 = f"{self.random_pkg_name}=={self.random_version}"
        other_pkg = f"dep-{uuid.uuid4().hex[:6]}==1.0.0"

        stream_content = f"{comment_line}\n\n{pkg_line_1}\n{other_pkg}\n".encode("utf-8")
        stream = io.BytesIO(stream_content)

        results = self.parser.parse_stream(stream)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["name"], self.random_pkg_name)
        self.assertEqual(results[1]["name"].startswith("dep-"), True)

    def test_module_level_parse_requirements(self):
        req_str = f"{self.random_pkg_name}=={self.random_version}"
        results = parse_requirements(req_str)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], self.random_pkg_name)
        self.assertEqual(results[0]["version"], self.random_version)

if __name__ == "__main__":
    unittest.main()