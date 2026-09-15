import unittest
from unittest.mock import patch
import io
import uuid
import random
from skills.dependency_parser import DependencyParser, parse_dependency_string

class TestDependencyParser(unittest.TestCase):
    def setUp(self):
        self.parser = DependencyParser()
        self.pkg_name = f"pkg-{uuid.uuid4().hex[:8]}"
        self.version_num = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.extra_name = f"ext-{uuid.uuid4().hex[:6]}"
        self.marker_var = f"sys_platform == '{uuid.uuid4().hex[:4]}'"

    @patch('skills.dependency_parser.Requirement')
    def test_parse_valid_dependency(self, mock_requirement_cls):
        dep_str = f"{self.pkg_name}>={self.version_num}; {self.marker_var}"

        mock_req = mock_requirement_cls.return_value
        mock_req.name = self.pkg_name
        mock_req.specifier = f">={self.version_num}"
        mock_req.marker = self.marker_var
        mock_req.extras = [self.extra_name]

        result = self.parser.parse(dep_str)

        self.assertEqual(result["name"], self.pkg_name)
        self.assertEqual(result["version_constraint"], f">={self.version_num}")
        self.assertEqual(result["version"], f">={self.version_num}")
        self.assertEqual(result["marker"], self.marker_var)
        self.assertIn(self.extra_name, result["extras"])

    def test_parse_empty_string_raises_value_error(self):
        invalid_inputs = ["", "   ", None]
        for inv in invalid_inputs:
            with self.assertRaises(ValueError):
                self.parser.parse(inv)

    @patch('skills.dependency_parser.Requirement', side_effect=Exception("Malformed"))
    def test_parse_malformed_string_raises_value_error(self, mock_requirement_cls):
        malformed_str = f"!!!invalid_dep_{uuid.uuid4().hex[:6]}"
        with self.assertRaises(ValueError):
            self.parser.parse(malformed_str)

    def test_parse_stream_with_valid_and_comment_lines(self):
        stream_content = f"# Comment line {uuid.uuid4().hex}\n{self.pkg_name}=={self.version_num}\n\n"
        stream = io.StringIO(stream_content)

        with patch('skills.dependency_parser.Requirement') as mock_req_cls:
            mock_req = mock_req_cls.return_value
            mock_req.name = self.pkg_name
            mock_req.specifier = f"=={self.version_num}"
            mock_req.marker = None
            mock_req.extras = []

            results = self.parser.parse_stream(stream)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["name"], self.pkg_name)

    def test_parse_stream_bytes(self):
        stream_content = f"{self.pkg_name}>={self.version_num}\n".encode('utf-8')
        stream = io.BytesIO(stream_content)

        with patch('skills.dependency_parser.Requirement') as mock_req_cls:
            mock_req = mock_req_cls.return_value
            mock_req.name = self.pkg_name
            mock_req.specifier = f">={self.version_num}"
            mock_req.marker = None
            mock_req.extras = []

            results = self.parser.parse_stream(stream)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["name"], self.pkg_name)

    def test_parse_batch(self):
        dep_list = [f"{self.pkg_name}=={self.version_num}"]
        with patch('skills.dependency_parser.Requirement') as mock_req_cls:
            mock_req = mock_req_cls.return_value
            mock_req.name = self.pkg_name
            mock_req.specifier = f"=={self.version_num}"
            mock_req.marker = None
            mock_req.extras = []

            results = self.parser.parse_batch(dep_list)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["name"], self.pkg_name)

    def test_parse_dependency_string_helper(self):
        dep_str = f"{self.pkg_name}~={self.version_num}"
        with patch('skills.dependency_parser.Requirement') as mock_req_cls:
            mock_req = mock_req_cls.return_value
            mock_req.name = self.pkg_name
            mock_req.specifier = f"~={self.version_num}"
            mock_req.marker = None
            mock_req.extras = []

            res = parse_dependency_string(dep_str)
            self.assertEqual(res["name"], self.pkg_name)