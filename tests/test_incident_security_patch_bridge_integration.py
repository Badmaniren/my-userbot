import unittest
import uuid
import random
from skills.incident_security_patch_bridge import (
    incident_security_patch_bridge,
    auto_patch_pipeline,
    vulnerability_scanner,
    vulnerability_patch_orchestrator,
    incident_aggregator
)

class TestIncidentSecurityPatchBridgeIntegration(unittest.TestCase):
    
    def test_end_to_end_defensive_pipeline_integration(self):
        dynamic_incident_id = f"INC-{uuid.uuid4().hex[:8].upper()}"
        dynamic_cve_code = f"CVE-2026-{random.randint(1000, 9999)}"
        
        payload = {
            "incident_id": dynamic_incident_id,
            "vulnerability_vector": dynamic_cve_code,
            "severity_score": round(random.uniform(7.0, 10.0), 1)
        }
        
        scan_result = vulnerability_scanner(payload)
        self.assertIsInstance(scan_result, dict)
        
        agg_result = incident_aggregator(payload)
        self.assertIsInstance(agg_result, dict)
        
        bridge_result = incident_security_patch_bridge(payload)
        
        self.assertIsInstance(bridge_result, dict)
        self.assertTrue(bridge_result.get("patch_pipeline_triggered"))
        self.assertEqual(bridge_result.get("target_incident_id"), dynamic_incident_id)
        self.assertEqual(bridge_result.get("status"), "success")
        self.assertIn("token", bridge_result)
        self.assertIn("value", bridge_result)
        
        orchestrator_payload = {
            "incident_id": dynamic_incident_id,
            "bridge_token": bridge_result["token"],
            "bridge_value": bridge_result["value"]
        }
        
        patch_exec_result = auto_patch_pipeline(orchestrator_payload)
        self.assertIsInstance(patch_exec_result, dict)
        
        vuln_patch_result = vulnerability_patch_orchestrator(orchestrator_payload)
        self.assertIsInstance(vuln_patch_result, dict)

if __name__ == "__main__":
    unittest.main()