import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string
from skills.package_requirement_extractor import (
    extract_requirements,
    normalize_requirement,
    PackageRequirementExtractor
)

class TestPackageRequirementExtractor(unittest.TestCase):

    def setUp(self):
        self.extractor = PackageRequirementExtractor()
        self.random_pkg_name = ''.join(random.choices(string.ascii_lowercase, k=10)) + '_' + uuid.uuid4().hex[:6]

    def test_normalize_requirement_valid(self):
        raw_req = f"{self.random_pkg_name} >= 1.2.3, < 2.0.0; python_version < '3.10'"
        normalized = normalize_requirement(raw_req)
        self.assertIsNotNone(normalized)
        self.assertIn(self.random_pkg_name, normalized)

    def test_normalize_requirement_malformed(self):
        gibberish = uuid.uuid4().hex + '@@@invalid_req!_#'
        with self.assertRaises(ValueError):
            normalize_requirement(gibberish, strict=True)
        
        result_lenient = normalize_requirement(gibberish, strict=False)
        self.assertIsNone(result_lenient)

    def test_extract_requirements_from_stream(self):
        req1 = f"pkg-{uuid.uuid4().hex[:4]}==1.0.0"
        req2 = f"pkg-{uuid.uuid4().hex[:4]}>=2.1.0"
        stream_content = f"{req1}\n# Comment line\n{req2}\n".encode('utf-8')
        
        stream = io.BytesIO(stream_content)
        extracted = self.extractor.extract_from_stream(stream)
        
        self.assertIn(req1, extracted)
        self.assertIn(req2, extracted)
        self.assertEqual(len(extracted), 2)

    def test_extract_requirements_with_error_no_swallowing(self):
        malicious_stream = io.BytesIO(b'\xff\xfe\xfd invalid encoding stream bytes')
        
        with patch('skills.package_requirement_extractor.logger') as mock_logger:
            try:
                self.extractor.extract_from_stream(malicious_stream, raise_on_error=True)
            except Exception as e:
                self.assertIsNotNone(e)
            
            mock_logger.error.assert_called()

    def test_extractor_instance_methods_and_random_parsing(self):
        unique_dep = f"dep-{uuid.uuid4().hex[:8]} [security,dev] >= 3.0.0"
        mock_metadata = {
            "requires_dist": [
                unique_dep,
                f"unrelated-package-{uuid.uuid4().hex[:6]}"
            ]
        }
        
        result = self.extractor.extract_from_metadata(mock_metadata)
        self.assertTrue(any(unique_dep in r for r in result))

    def test_stream_read_failure_simulation(self):
        faulty_stream = MagicMock()
        faulty_stream.read.side_effect = IOError(f"Read failed for {uuid.uuid4().hex}")
        
        with self.assertRaises(IOError):
            self.extractor.extract_from_stream(faulty_stream)