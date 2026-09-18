import unittest
from unittest.mock import patch
import uuid
import random
import io
import string

from skills.incident_security_patch_bridge import (
    incident_security_patch_bridge,
    _dummy_func
)

class TestIncidentSecurityPatchBridge(unittest.TestCase):

    def setUp(self):
        self.random_prefix = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.incident_id = f"inc_{uuid.uuid4().hex[:10]}"
        self.payload = {
            "incident_id": self.incident_id,
            "metadata": f"{self.random_prefix}_data"
        }

    def test_incident_security_patch_bridge_with_valid_dict(self):
        result = incident_security_patch_bridge(self.payload)
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("patch_pipeline_triggered"))
        self.assertEqual(result.get("target_incident_id"), self.incident_id)
        self.assertEqual(result.get("status"), "success")
        self.assertIn("token", result)
        self.assertIn("value", result)

    def test_incident_security_patch_bridge_with_none_payload(self):
        result = incident_security_patch_bridge(None)
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("patch_pipeline_triggered"))
        self.assertIsNone(result.get("target_incident_id"))
        self.assertEqual(result.get("status"), "success")

    def test_incident_security_patch_bridge_with_invalid_payload_type(self):
        invalid_payload = random.randint(10000, 99999)
        result = incident_security_patch_bridge(invalid_payload)
        self.assertIsInstance(result, dict)
        self.assertIsNone(result.get("target_incident_id"))

    def test_dummy_func_behavior(self):
        res = _dummy_func()
        self.assertIsInstance(res, dict)
        self.assertEqual(res.get("status"), "success")
        self.assertIn("token", res)
        self.assertIn("value", res)

    def test_stream_and_io_integration_mocking(self):
        random_bytes = f"{uuid.uuid4().hex}".encode('utf-8')
        mock_stream = io.BytesIO(random_bytes)
        
        with patch('skills.incident_security_patch_bridge.random.randint', return_value=42) as mock_rand:
            res = incident_security_patch_bridge(self.payload)
            self.assertEqual(res["value"], 42)
            mock_rand.assert_called_once()
        
        self.assertEqual(mock_stream.read(), random_bytes)

if __name__ == '__main__':
    unittest.main()