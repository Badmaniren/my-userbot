import unittest
import io
import uuid
import random
from unittest.mock import patch
from skills.package_requirement_parser import PackageRequirementParser, parse_requirement

class TestPackageRequirementParser(unittest.TestCase):

    def setUp(self):
        self.parser = PackageRequirementParser()
        self.pkg_prefix = f"pkg-{uuid.uuid4().hex[:6]}"
        self.version_str = f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.extra_name = f"ext-{uuid.uuid4().hex[:6]}"

    def test_parse_simple_package_name(self):
        req_line = self.pkg_prefix
        result = self.parser.parse(req_line)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('name'), self.pkg_prefix)
        self.assertIsNone(result.get('operator'))
        self.assertIsNone(result.get('version'))
        self.assertEqual(result.get('extras'), [])

    def test_parse_with_version_constraint(self):
        operator = random.choice(['==', '>=', '<=', '>', '<', '!='])
        req_line = f"{self.pkg_prefix} {operator} {self.version_str}"
        result = parse_requirement(req_line)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('name'), self.pkg_prefix)
        self.assertEqual(result.get('operator'), operator)
        self.assertEqual(result.get('version'), self.version_str)

    def test_parse_with_extras_and_environment_markers(self):
        marker_env = f"python_version < '{random.randint(3, 4)}.{random.randint(0, 9)}'"
        req_line = f"{self.pkg_prefix}[{self.extra_name}] >= {self.version_str}; {marker_env}"
        result = self.parser.parse(req_line)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('name'), self.pkg_prefix)
        self.assertIn(self.extra_name, result.get('extras'))
        self.assertEqual(result.get('operator'), '>=')
        self.assertEqual(result.get('version'), self.version_str)

    def test_parser_with_stream_input(self):
        comment_prefix = f"# comment-{uuid.uuid4().hex[:6]}"
        stream_content = f"{comment_prefix}\n{self.pkg_prefix}=={self.version_str}\n   \n"
        stream = io.BytesIO(stream_content.encode('utf-8'))

        results = list(self.parser.parse_stream(stream))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].get('name'), self.pkg_prefix)
        self.assertEqual(results[0].get('version'), self.version_str)

    def test_parse_stream_string_input(self):
        stream_content = f"{self.pkg_prefix}>={self.version_str}\n"
        stream = io.StringIO(stream_content)

        results = list(self.parser.parse_stream(stream))
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].get('name'), self.pkg_prefix)
        self.assertEqual(results[0].get('operator'), '>=')

if __name__ == '__main__':
    unittest.main()