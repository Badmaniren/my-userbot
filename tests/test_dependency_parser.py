import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.dependency_parser import DependencyParser, parse_requires_dist, parse_dependencies

class TestDependencyParser(unittest.TestCase):
    def setUp(self):
        self.parser = DependencyParser()
        self.random_name = f"pkg-{uuid.uuid4().hex[:8]}"
        self.random_version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.random_extra = f"ext-{uuid.uuid4().hex[:6]}"
        self.random_marker = f"python_version > '{random.randint(3, 8)}'"

    @patch('skills.dependency_parser.Requirement')
    def test_parse_success(self, mock_requirement_class):
        mock_req = MagicMock()
        mock_req.name = self.random_name
        mock_req.specifier = f">={self.random_version}"
        mock_req.extras = {self.random_extra}
        mock_req.marker = self.random_marker
        mock_requirement_class.return_value = mock_req

        raw_req_str = f"{self.random_name} >={self.random_version} [{self.random_extra}]; {self.random_marker}"
        result = self.parser.parse(raw_req_str)

        self.assertEqual(result["name"], self.random_name)
        self.assertEqual(result["specifiers"], f">={self.random_version}")
        self.assertIn(self.random_extra, result["extras"])
        self.assertEqual(result["marker"], self.random_marker)
        mock_requirement_class.assert_called_once_with(raw_req_str)

    @patch('skills.dependency_parser.Requirement')
    def test_parse_minimal(self, mock_requirement_class):
        mock_req = MagicMock()
        mock_req.name = self.random_name
        mock_req.specifier = ""
        mock_req.extras = None
        mock_req.marker = None
        mock_requirement_class.return_value = mock_req

        result = self.parser.parse(self.random_name)

        self.assertEqual(result["name"], self.random_name)
        self.assertEqual(result["specifiers"], "")
        self.assertEqual(result["extras"], [])
        self.assertIsNone(result["marker"])

    def test_parse_stream(self):
        line1 = f"{self.random_name}-one >= 1.0.0"
        line2 = f"# {uuid.uuid4().hex}"
        line3 = f"{self.random_name}-two == 2.0.0"

        stream_content = f"{line1}\n{line2}\n\n{line3}\n".encode('utf-8')
        stream = io.BytesIO(stream_content)

        with patch.object(self.parser, 'parse') as mock_parse:
            mock_parse.side_effect = [
                {"name": f"{self.random_name}-one", "specifiers": ">=1.0.0", "extras": [], "marker": None},
                {"name": f"{self.random_name}-two", "specifiers": "==2.0.0", "extras": [], "marker": None}
            ]

            results = self.parser.parse_stream(stream)

            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["name"], f"{self.random_name}-one")
            self.assertEqual(results[1]["name"], f"{self.random_name}-two")
            self.assertEqual(mock_parse.call_count, 2)

    def test_build_graph(self):
        dep1 = f"{self.random_name}-alpha >= 1.2.3"
        dep2 = f"{self.random_name}-beta < 3.0.0"
        dep_list = [dep1, dep2]

        parsed_alpha = {"name": f"{self.random_name}-alpha", "specifiers": ">=1.2.3", "extras": [], "marker": None}
        parsed_beta = {"name": f"{self.random_name}-beta", "specifiers": "<3.0.0", "extras": [], "marker": None}

        with patch.object(self.parser, 'parse') as mock_parse:
            mock_parse.side_effect = [parsed_alpha, parsed_beta]

            graph = self.parser.build_graph(dep_list)

            self.assertIn(f"{self.random_name}-alpha", graph)
            self.assertIn(f"{self.random_name}-beta", graph)
            self.assertEqual(graph[f"{self.random_name}-alpha"], parsed_alpha)
            self.assertEqual(graph[f"{self.random_name}-beta"], parsed_beta)
            self.assertEqual(mock_parse.call_count, 2)

    @patch('skills.dependency_parser.DependencyParser.parse')
    def test_parse_requires_dist_helper(self, mock_parse):
        expected_dict = {
            "name": self.random_name,
            "specifiers": f"=={self.random_version}",
            "extras": [self.random_extra],
            "marker": None
        }
        mock_parse.return_value = expected_dict

        raw_str = f"{self.random_name}=={self.random_version}"
        res = parse_requires_dist(raw_str)

        self.assertEqual(res, expected_dict)
        mock_parse.assert_called_once_with(raw_str)

    @patch('skills.dependency_parser.DependencyParser.parse')
    def test_parse_dependencies_helper(self, mock_parse):
        dep_name_1 = f"{uuid.uuid4().hex[:5]}"
        dep_name_2 = f"{uuid.uuid4().hex[:5]}"
        raw_list = [dep_name_1, dep_name_2]

        parsed_1 = {"name": dep_name_1, "specifiers": "", "extras": [], "marker": None}
        parsed_2 = {"name": dep_name_2, "specifiers": "", "extras": [], "marker": None}
        mock_parse.side_effect = [parsed_1, parsed_2]

        res = parse_dependencies(raw_list)

        self.assertEqual(res, [parsed_1, parsed_2])
        self.assertEqual(mock_parse.call_count, 2)