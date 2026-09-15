import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
from skills.requirement_analyzer import RequirementAnalyzer, PEP508Specifier

class TestRequirementAnalyzer(unittest.TestCase):
    
    def setUp(self):
        self.rand_name = f"pkg-{uuid.uuid4().hex[:8]}"
        self.rand_version = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.rand_operator = random.choice([">=", "==", "<=", ">", "<", "~="])
        self.raw_spec = f"{self.rand_name} {self.rand_operator} {self.rand_version}"

    def test_pep508_specifier_get(self):
        spec = PEP508Specifier(self.rand_name, self.rand_operator, self.rand_version)
        self.assertEqual(spec.get("name"), self.rand_name)
        self.assertIsNone(spec.get(uuid.uuid4().hex))

    @patch('skills.requirement_analyzer.Requirement')
    def test_analyzer_init_and_parse_single(self, mock_requirement_class):
        mock_req_instance = MagicMock()
        mock_req_instance.name = self.rand_name
        mock_req_instance.extras = [uuid.uuid4().hex]
        
        mock_spec = MagicMock()
        mock_spec.operator = self.rand_operator
        mock_spec.version = self.rand_version
        mock_req_instance.specifier = [mock_spec]
        
        mock_requirement_class.return_value = mock_req_instance

        analyzer = RequirementAnalyzer(self.raw_spec)
        self.assertEqual(analyzer.name, self.rand_name)
        self.assertEqual(analyzer.operator, self.rand_operator)
        self.assertEqual(analyzer.version, self.rand_version)
        self.assertEqual(analyzer.extras, mock_req_instance.extras)

        parsed_list = analyzer.parse(self.raw_spec)
        self.assertEqual(len(parsed_list), 1)
        self.assertEqual(parsed_list[0].name, self.rand_name)

    @patch('skills.requirement_analyzer.Requirement')
    def test_analyzer_init_empty_specifier(self, mock_requirement_class):
        mock_req_instance = MagicMock()
        mock_req_instance.name = self.rand_name
        mock_req_instance.extras = []
        mock_req_instance.specifier = []
        mock_requirement_class.return_value = mock_req_instance

        analyzer = RequirementAnalyzer(self.raw_spec)
        self.assertEqual(analyzer.operator, "==")
        self.assertEqual(analyzer.version, "")

    @patch('skills.requirement_analyzer.SpecifierSet')
    def test_match(self, mock_specifier_set_class):
        mock_spec_set = MagicMock()
        target_version = f"{random.randint(1, 5)}.0.0"
        mock_spec_set.__contains__.return_value = True
        mock_specifier_set_class.return_value = mock_spec_set

        analyzer = RequirementAnalyzer()
        self.assertTrue(analyzer.match(target_version))

        analyzer.operator = ">="
        analyzer.version = "1.0.0"
        res = analyzer.match(target_version)
        self.assertTrue(res)
        mock_specifier_set_class.assert_called_with(">=1.0.0")

    @patch('skills.requirement_analyzer.Requirement')
    def test_parse_stream_bytes(self, mock_requirement_class):
        mock_req_instance = MagicMock()
        mock_req_instance.name = self.rand_name
        mock_req_instance.extras = []
        mock_spec = MagicMock()
        mock_spec.operator = "=="
        mock_spec.version = self.rand_version
        mock_req_instance.specifier = [mock_spec]
        mock_requirement_class.return_value = mock_req_instance

        comment_line = f"# {uuid.uuid4().hex}"
        stream_content = f"{comment_line}\n{self.raw_spec}\n"
        stream = io.BytesIO(stream_content.encode('utf-8'))

        analyzer = RequirementAnalyzer()
        results = analyzer.parse_stream(stream)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, self.rand_name)

    @patch('skills.requirement_analyzer.Requirement')
    def test_parse_stream_string(self, mock_requirement_class):
        mock_req_instance = MagicMock()
        mock_req_instance.name = self.rand_name
        mock_req_instance.extras = []
        mock_spec = MagicMock()
        mock_spec.operator = "=="
        mock_spec.version = self.rand_version
        mock_req_instance.specifier = [mock_spec]
        mock_requirement_class.return_value = mock_req_instance

        stream_content = f"   \n{self.raw_spec}\n"
        stream = io.StringIO(stream_content)

        analyzer = RequirementAnalyzer()
        results = analyzer.parse_stream(stream)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, self.rand_name)

    @patch('skills.requirement_analyzer.Requirement')
    def test_parse_stream_raw_string(self, mock_requirement_class):
        mock_req_instance = MagicMock()
        mock_req_instance.name = self.rand_name
        mock_req_instance.extras = []
        mock_spec = MagicMock()
        mock_spec.operator = "=="
        mock_spec.version = self.rand_version
        mock_req_instance.specifier = [mock_spec]
        mock_requirement_class.return_value = mock_req_instance

        analyzer = RequirementAnalyzer()
        results = analyzer.parse_stream(self.raw_spec)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, self.rand_name)