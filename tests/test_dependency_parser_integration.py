import unittest
import io
import uuid
import random
from skills.dependency_parser import DependencyParser, parse_dependency, parse_dependency_string
from skills.pypi_client import PyPIClient

class TestDependencyParserIntegration(unittest.TestCase):
    def setUp(self):
        self.parser = DependencyParser()
        self.pypi_client = PyPIClient()
        self.random_tag = uuid.uuid4().hex[:8]

    def test_parse_single_requirement_real_data(self):
        pkg_name = f"requests-{self.random_tag}"
        ver = f"{random.randint(1, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        raw_req = f"{pkg_name} (>={ver})"

        result = self.parser.parse(raw_req)

        self.assertEqual(result['name'], pkg_name)
        self.assertEqual(result['operator'], '>=')
        self.assertEqual(result['version'], ver)
        self.assertIsInstance(result['extras'], list)

    def test_parse_stream_integration_with_bytes_io(self):
        target_pkg = f"pkg-{self.random_tag}"
        target_ver = f"1.{random.randint(0, 5)}.0"
        stream_content = f"""
        # Comment line
        {target_pkg} == {target_ver} ; python_version < "3.10"
        invalid_requirement_string_xyz_[[[
        numpy >= 1.20.0 # inline comment
        """
        stream = io.BytesIO(stream_content.encode('utf-8'))

        results = self.parser.parse_stream(stream)

        self.assertGreaterEqual(len(results), 2)

        names = [r['name'] for r in results]
        self.assertIn(target_pkg, names)
        self.assertIn('numpy', names)

        for r in results:
            if r['name'] == target_pkg:
                self.assertEqual(r['operator'], '==')
                self.assertEqual(r['version'], target_ver)
                self.assertIsNotNone(r['marker'])

    def test_convenience_functions_behavior(self):
        rand_val = random.randint(100, 999)
        req_str = f"fastapi (>=0.{rand_val}.0)"

        res1 = parse_dependency(req_str)
        self.assertEqual(res1['name'], 'fastapi')
        self.assertEqual(res1['operator'], '>=')

        res2 = parse_dependency_string(req_str)
        self.assertIsNotNone(res2)
        self.assertEqual(res2['name'], 'fastapi')

        res_invalid = parse_dependency_string("---invalid---req---")
        self.assertIsNone(res_invalid)

    def test_pypi_client_dependency_parsing_chain(self):
        # Проверяем сквозную интеграцию с pypi_client без моков
        versions = self.pypi_client.get_release_versions("pip")
        self.assertIsInstance(versions, list)
        if versions:
            test_version = random.choice(versions[:5])
            deps = self.pypi_client.get_dependencies("pip", test_version)
            self.assertIsInstance(deps, list)
            if deps:
                raw_dep = random.choice(deps)
                parsed = self.parser.parse(raw_dep)
                self.assertIn('name', parsed)
                self.assertIn('operator', parsed)
                self.assertIn('version', parsed)

if __name__ == '__main__':
    unittest.main()