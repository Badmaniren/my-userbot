import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.requirement_analyzer import RequirementAnalyzer, PEP508Specifier

class TestRequirementAnalyzerInquisitor(unittest.TestCase):

    def setUp(self):
        self.pkg_name = f"pkg-{uuid.uuid4().hex[:8]}"
        self.operator = random.choice(['==', '>=', '<=', '>', '<', '!=', '~='])
        self.version_num = f"{random.randint(0, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.raw_spec = f"{self.pkg_name} {self.operator} {self.version_num}"

    def test_analyzer_initialization_with_random_spec(self):
        analyzer = RequirementAnalyzer(self.raw_spec)
        self.assertEqual(analyzer.name, self.pkg_name)
        self.assertEqual(analyzer.operator, self.operator)
        self.assertEqual(analyzer.version, self.version_num)

    def test_specifier_matching_success(self):
        analyzer = RequirementAnalyzer(f"secure-lib == 1.2.3")
        self.assertTrue(analyzer.match("1.2.3"))

    def test_specifier_matching_failure(self):
        rand_ver = f"{random.randint(10, 20)}.0.0"
        analyzer = RequirementAnalyzer(f"{self.pkg_name} == {self.version_num}")
        self.assertFalse(analyzer.match(rand_ver))

    def test_pep508_parsing_edge_cases(self):
        extra_tag = ''.join(random.choices(string.ascii_lowercase, k=6))
        complex_spec = f"{self.pkg_name}[{extra_tag}] >= 2.0.0"
        
        with patch('skills.requirement_analyzer.parse_requirement') as mock_parse:
            mock_parse.return_value = MagicMock(
                name=self.pkg_name,
                specifier=MagicMock(<strong>iter</strong>=lambda x: iter([MagicMock(operator='>=', version='2.0.0')])),
                extras=[extra_tag]
            )
            analyzer = RequirementAnalyzer(complex_spec)
            self.assertEqual(analyzer.name, self.pkg_name)
            self.assertIn(extra_tag, analyzer.extras)

    def test_stream_parsing_with_random_bytes(self):
        random_content = f"{self.pkg_name} >= {self.version_num}\n".encode('utf-8')
        stream = io.BytesIO(random_content)
        
        analyzer = RequirementAnalyzer()
        parsed_list = analyzer.parse_stream(stream)
        
        self.assertTrue(any(p.name == self.pkg_name for p in parsed_list))

    def compatibility_matrix_validation(self):
        versions = [f"1.{i}.0" for i in range(5)]
        target_ver = random.choice(versions)
        analyzer = RequirementAnalyzer(f"{self.pkg_name} == {target_ver}")
        
        results = [analyzer.match(v) for v in versions]
        self.assertEqual(results.count(True), 1)
        self.assertTrue(results[versions.index(target_ver)])

if __name__ == '__main__':
    unittest.main()