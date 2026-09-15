import unittest
from unittest.mock import patch, MagicMock
import io
import json
import uuid
import random
from skills.package_spec_parser import (
    PackageSpec,
    parse_package_spec,
    PackageSpecParser,
    PyPIClient
)

class TestPackageSpecParser(unittest.TestCase):

    def test_package_spec_init_and_get(self):
        rand_name = f"pkg-{uuid.uuid4().hex[:8]}"
        rand_version = f">={random.randint(1, 3)}.{random.randint(0, 9)}"
        rand_extra = f"extra-{uuid.uuid4().hex[:6]}"
        rand_marker = f"python_version < '{random.randint(3, 8)}'"

        spec = PackageSpec(
            name=rand_name,
            version=rand_version,
            extras=[rand_extra],
            marker=rand_marker
        )

        self.assertEqual(spec.name, rand_name)
        self.assertEqual(spec.version, rand_version)
        self.assertEqual(spec.extras, [rand_extra])
        self.assertEqual(spec.marker, rand_marker)
        self.assertEqual(spec.get("name"), rand_name)
        self.assertEqual(spec.get("version"), rand_version)
        self.assertEqual(spec.get("extras"), [rand_extra])
        self.assertEqual(spec.get("marker"), rand_marker)
        self.assertIsNone(spec.get("non_existent_key"))

    def test_parse_package_spec_empty(self):
        self.assertIsNone(parse_package_spec(""))
        self.assertIsNone(parse_package_spec("   "))
        self.assertIsNone(parse_package_spec(None))

    @patch("skills.package_spec_parser.Requirement")
    def test_parse_package_spec_valid(self, mock_requirement_class):
        rand_name = f"lib-{uuid.uuid4().hex[:6]}"
        rand_ver_spec = f"=={random.randint(1, 5)}.0"
        rand_marker_str = f"sys_platform == '{uuid.uuid4().hex[:4]}'"
        rand_extra_val = f"feat-{uuid.uuid4().hex[:4]}"

        mock_req_instance = MagicMock()
        mock_req_instance.name = rand_name
        mock_req_instance.specifier = rand_ver_spec
        mock_req_instance.marker = rand_marker_str
        mock_req_instance.extras = {rand_extra_val}
        mock_requirement_class.return_value = mock_req_instance

        input_str = f"({rand_name} {rand_ver_spec} ; {rand_marker_str})"
        result = parse_package_spec(input_str)

        mock_requirement_class.assert_called_once_with(f"{rand_name} {rand_ver_spec} ; {rand_marker_str}")
        self.assertIsInstance(result, PackageSpec)
        self.assertEqual(result.name, rand_name)
        self.assertEqual(result.version, str(rand_ver_spec))
        self.assertEqual(result.marker, str(rand_marker_str))
        self.assertIn(rand_extra_val, result.extras)

    def test_package_spec_parser_parse(self):
        parser = PackageSpecParser()
        rand_name = f"module-{uuid.uuid4().hex[:6]}"
        with patch("skills.package_spec_parser.Requirement") as mock_req:
            mock_instance = MagicMock()
            mock_instance.name = rand_name
            mock_instance.specifier = ""
            mock_instance.marker = ""
            mock_instance.extras = []
            mock_req.return_value = mock_instance

            res = parser.parse(rand_name)
            self.assertIsInstance(res, PackageSpec)
            self.assertEqual(res.name, rand_name)

    def test_package_spec_parser_parse_stream(self):
        parser = PackageSpecParser()
        rand_names = [f"dep-{uuid.uuid4().hex[:6]}" for _ in range(3)]
        stream_lines = [
            f"   \n",
            f"{rand_names[0]}\n",
            f"b'{rand_names[1]}'\n".encode('utf-8'),
            f"({rand_names[2]})\n"
        ]

        with patch("skills.package_spec_parser.Requirement") as mock_req:
            def side_effect(arg):
                m = MagicMock()
                clean_arg = arg.strip()
                if clean_arg.startswith('b\''):
                    clean_arg = clean_arg[2:-1]
                if clean_arg.startswith('(') and clean_arg.endswith(')'):
                    clean_arg = clean_arg[1:-1].strip()
                m.name = clean_arg
                m.specifier = None
                m.marker = None
                m.extras = []
                return m
            mock_req.side_effect = side_effect

            results = parser.parse_stream(stream_lines)
            self.assertEqual(len(results), 3)
            self.assertEqual(results[0].name, rand_names[0])
            self.assertEqual(results[1].name, rand_names[1])
            self.assertEqual(results[2].name, rand_names[2])

    def test_pypi_client_parse_stream_data_bytes(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        payload = json.dumps({rand_key: rand_val}).encode('utf-8')
        stream = io.BytesIO(payload)

        client = PyPIClient()
        data = client.parse_stream_data(stream)
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get(rand_key), rand_val)

    def test_pypi_client_parse_stream_data_string(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        payload_str = json.dumps({rand_key: rand_val})
        stream = io.BytesIO(payload_str.encode('utf-8'))

        class StringReaderStream:
            def __init__(self, content):
                self.content = content
            def read(self):
                return self.content

        custom_stream = StringReaderStream(payload_str)
        client = PyPIClient()
        data = client.parse_stream_data(custom_stream)
        self.assertIsInstance(data, dict)
        self.assertEqual(data.get(rand_key), rand_val)