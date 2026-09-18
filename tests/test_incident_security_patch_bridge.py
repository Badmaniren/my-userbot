import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.incident_security_patch_bridge import incident_security_patch_bridge


class TestIncidentSecurityPatchBridge(unittest.TestCase):

    def test_incident_security_patch_bridge_with_valid_dict_payload(self):
        rand_incident_id = uuid.uuid4().hex
        payload = {
            "".join(random.choices(string.ascii_lowercase, k=8)): "".join(random.choices(string.ascii_lowercase, k=10)),
            "incident_id": rand_incident_id
        }

        result = incident_security_patch_bridge(payload)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("patch_pipeline_triggered"))
        self.assertEqual(result.get("target_incident_id"), rand_incident_id)
        self.assertEqual(result.get("status"), "success")
        self.assertIn("token", result)
        self.assertIn("value", result)

    def test_incident_security_patch_bridge_with_invalid_payload_type(self):
        rand_payload = random.randint(10000, 99999)

        result = incident_security_patch_bridge(rand_payload)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("patch_pipeline_triggered"))
        self.assertIsNone(result.get("target_incident_id"))
        self.assertEqual(result.get("status"), "success")
        self.assertIsInstance(result.get("token"), str)
        self.assertIsInstance(result.get("value"), int)

    def test_incident_security_patch_bridge_with_empty_dict_payload(self):
        payload = {}

        result = incident_security_patch_bridge(payload)

        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("patch_pipeline_triggered"))
        self.assertIsNone(result.get("target_incident_id"))
        self.assertEqual(result.get("status"), "success")
        self.assertIsNotNone(result.get("token"))

    def test_incident_security_patch_bridge_io_stream_mocking(self):
        rand_bytes = "".join(random.choices(string.ascii_letters, k=50)).encode("utf-8")
        stream = io.BytesIO(rand_bytes)

        payload = {
            "incident_id": uuid.uuid4().hex,
            "stream_data": stream.read().decode("utf-8")
        }

        result = incident_security_patch_bridge(payload)

        self.assertEqual(result["target_incident_id"], payload["incident_id"])
        self.assertEqual(result["status"], "success")

    def test_incident_security_patch_bridge_random_execution_flow(self):
        rand_id = uuid.uuid4().hex
        payload = {"incident_id": rand_id}

        with patch("skills.incident_security_patch_bridge.uuid.uuid4") as mock_uuid:
            mock_token = uuid.uuid4().hex
            mock_uuid.return_value.hex = mock_token
            
            with patch("skills.incident_security_patch_bridge.random.randint") as mock_rand:
                rand_val = random.randint(100, 500)
                mock_rand.return_value = rand_val

                result = incident_security_patch_bridge(payload)

                self.assertEqual(result["token"], mock_token)
                self.assertEqual(result["value"], rand_val)
                self.assertEqual(result["target_incident_id"], rand_id)


if __name__ == "__main__":
    unittest.main()