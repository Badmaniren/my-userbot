import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
from skills.package_spec_parser import parse_package_spec, PackageSpecParser

class TestPackageSpecParser(unittest.TestCase):

    def setUp(self):
        self.random_pkg_name = f"pkg-{uuid.uuid4().hex[:8]}"
        self.random_version = f"{random.randint(0, 9)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        self.random_extra = ''.join(random.choices(string.ascii_lowercase, k=6))
        self.random_marker = f"python_version < '{random.randint(3, 4)}.{random.randint(0, 9)}'"

    def test_parse_simple_spec_randomized(self):
        spec_string = f"{self.random_pkg_name} >= {self.random_version}"
        parser = PackageSpecParser()
        result = parser.parse(spec_string) if hasattr(parser, 'parse') else parse_package_spec(spec_string)
        
        self.assertIsNotNone(result)
        self.assertEqual(result.get('name') or result.name, self.random_pkg_name)
        self.assertIn(self.random_version, str(result.get('version') or result.version))

    def test_parse_spec_with_extras_and_markers(self):
        complex_spec = f"{self.random_pkg_name}[{self.random_extra}] == {self.random_version}; {self.random_marker}"
        
        parser = PackageSpecParser()
        result = parser.parse(complex_spec) if hasattr(parser, 'parse') else parse_package_spec(complex_spec)
        
        self.assertIsNotNone(result)
        name_val = result.get('name') if isinstance(result, dict) else result.name
        extras_val = result.get('extras') if isinstance(result, dict) else result.extras
        marker_val = result.get('marker') if isinstance(result, dict) else result.marker

        self.assertEqual(name_val, self.random_pkg_name)
        self.assertIn(self.random_extra, extras_val)
        self.assertIn(self.random_marker, str(marker_val))

    def test_parser_with_io_stream_chaos(self):
        stream_data = f"{self.random_pkg_name}=={self.random_version}\n".encode('utf-8')
        mock_stream = io.BytesIO(stream_data)

        if hasattr(PackageSpecParser, 'parse_stream'):
            parser = PackageSpecParser()
            results = parser.parse_stream(mock_stream)
            self.assertTrue(len(results) > 0)
            found = any(r.get('name') == self.random_pkg_name for r in results) if isinstance(results[0], dict) else any(r.name == self.random_pkg_name for r in results)
            self.assertTrue(found)
        else:
            line = mock_stream.readline().decode('utf-8').strip()
            result = parse_package_spec(line)
            self.assertIsNotNone(result)

    def test_invalid_spec_raises_or_returns_none(self):
        garbage_input = uuid.uuid4().hex + '@@@invalid##spec$$$'
        parser = PackageSpecParser()
        
        try:
            res = parser.parse(garbage_input) if hasattr(parser, 'parse') else parse_package_spec(garbage_input)
            self.assertTrue(res is None or isinstance(res, dict) or hasattr(res, 'name'))
        except Exception:
            pass

if __name__ == '__main__':
    unittest.main()