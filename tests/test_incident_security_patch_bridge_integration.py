import unittest
import uuid
import random
from skills.incident_security_patch_bridge import incident_security_patch_bridge

class TestIncidentSecurityPatchBridgeIntegration(unittest.TestCase):
    def test_patch_bridge_integration_with_real_payload(self):
        dynamic_incident_id = str(uuid.uuid4())
        random_payload_value = random.randint(100, 99999)
        
        payload = {
            "incident_id": dynamic_incident_id,
            "metric_threshold": random_payload_value,
            "source": "integration_test_suite"
        }
        
        response = incident_security_patch_bridge(payload)
        
        self.assertIsInstance(response, dict)
        self.assertEqual(response.get("status"), "success")
        self.assertTrue(response.get("patch_pipeline_triggered"))
        self.assertEqual(response.get("target_incident_id"), dynamic_incident_id)
        
        self.assertIn("token", response)
        self.assertIsInstance(response["token"], str)
        self.assertEqual(len(response["token"]), 32)
        
        self.assertIn("value", response)
        self.assertIsInstance(response["value"], int)
        self.assertTrue(1 <= response["value"] <= 1000)

if __name__ == "__main__":
    unittest.main()