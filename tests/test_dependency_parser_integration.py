import unittest
import uuid
import random
import io
from skills.dependency_parser import DependencyParser, parse_dependency

class TestDependencyParserIntegration(unittest.TestCase):
    def setUp(self):
        self.parser = DependencyParser()
        self.random_suffix = str(uuid.uuid4())[:8]

    def test_parse_valid_requirement(self):
        pkg_name = f"requests-{self.random_suffix}"
        version = f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        req_str = f"{pkg_name} (>={version})"
        
        result = self.parser.parse(req_str)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['name'], pkg_name)
        self.assertEqual(result['version_constraint'], f">={version}")
        self.assertEqual(result['constraints'], f">={version}")
        self.assertEqual(result['extras'], [])
        self.assertIsNone(result['marker'])

    def test_parse_stream_integration(self):
        pkg_1 = f"pkg-alpha-{self.random_suffix}"
        pkg_2 = f"pkg-beta-{self.random_suffix}"
        
        stream_data = f"# Comment line\n{pkg_1}==1.0.0\n\n{pkg_2}>=2.0.0; python_version < '3.10'\n".encode('utf-8')
        stream = io.BytesIO(stream_data)
        
        results = self.parser.parse_stream(stream)
        
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 2)
        
        self.assertEqual(results[0]['name'], pkg_1)
        self.assertEqual(results[0]['version_constraint'], "==1.0.0")
        
        self.assertEqual(results[1]['name'], pkg_2)
        self.assertEqual(results[1]['version_constraint'], ">=2.0.0")
        self.assertIn("python_version", results[1]['marker'])

    def test_parse_fallback_mechanism(self):
        malformed_req = f"invalid_req_syntax_{self.random_suffix} !@#$"
        
        result = parse_dependency(malformed_req)
        
        self.assertIsInstance(result, dict)
        self.assertTrue(result['name'].startswith("invalid_req_syntax"))
        self.assertIsNone(result['constraints'])
        self.assertIsNone(result['version_constraint'])
        self.assertEqual(result['extras'], [])
        self.assertIsNone(result['marker'])

if __name__ == '__main__':
    unittest.main()