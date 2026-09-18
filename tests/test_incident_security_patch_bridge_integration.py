import unittest
import uuid
import random
import os
from skills.incident_security_patch_bridge import incident_security_patch_bridge
from skills.incident_aggregator import incident_aggregator
from skills.auto_patch_pipeline import auto_patch_pipeline

class TestIncidentSecurityPatchBridgeIntegration(unittest.TestCase):
    def test_end_to_end_patch_bridging_flow(self):
        unique_incident_id = str(uuid.uuid4())
        unique_cve_code = f"CVE-2026-{random.randint(1000, 9999)}"
        severity_levels = ["CRITICAL", "HIGH", "MODERATE"]
        selected_severity = random.choice(severity_levels)

        incident_payload = {
            "incident_id": unique_incident_id,
            "vulnerability_id": unique_cve_code,
            "severity": selected_severity,
            "status": "CONFIRMED",
            "affected_component": f"service_node_{random.randint(1, 100)}"
        }

        aggregation_result = incident_aggregator(incident_payload)
        self.assertIsNotNone(aggregation_result, "Incident aggregator failed to process input.")

        bridge_response = incident_security_patch_bridge(aggregation_result)
        self.assertIsNotNone(bridge_response, "Incident security patch bridge returned None.")
        self.assertIn("patch_pipeline_triggered", bridge_response)
        self.assertEqual(bridge_response.get("target_incident_id"), unique_incident_id)

        pipeline_config = {
            "pipeline_id": str(uuid.uuid4()),
            "cve": unique_cve_code,
            "action": "AUTO_APPLY_PATCH"
        }
        pipeline_output = auto_patch_pipeline(pipeline_config)
        self.assertIsNotNone(pipeline_output)
        self.assertTrue(pipeline_output.get("success", True), "Auto patch pipeline execution failed.")

if __name__ == "__main__":
    unittest.main()