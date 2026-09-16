import unittest
import uuid
import random
import os
from skills.incident_recovery_workflow_orchestrator import (
    error_recovery_hub,
    incident_aggregator,
    incident_severity_evaluator,
    incident_impact_analyzer,
    incident_auto_recovery_dispatcher,
    auto_patch_pipeline,
    patch_validator,
    incident_notification_bridge,
    recovery_dashboard_generator
)

class TestIncidentRecoveryWorkflowIntegration(unittest.TestCase):
    def test_end_to_end_recovery_pipeline(self):
        unique_error_id = str(uuid.uuid4())
        random_error_code = f"ERR_{random.randint(1000, 9999)}"
        error_payload = {
            "error_id": unique_error_id,
            "code": random_error_code,
            "message": "Integration test runtime fault",
            "severity_score": random.uniform(5.0, 10.0)
        }

        hub_response = error_recovery_hub(error_payload)
        self.assertIsNotNone(hub_response)

        aggregated_incident = incident_aggregator(error_payload)
        self.assertEqual(aggregated_incident.get("error_id"), unique_error_id)

        severity_result = incident_severity_evaluator(aggregated_incident)
        self.assertIn("severity_level", severity_result)

        impact_report = incident_impact_analyzer(aggregated_incident)
        self.assertIsInstance(impact_report, dict)

        dispatch_result = incident_auto_recovery_dispatcher(aggregated_incident)
        self.assertTrue(dispatch_result.get("dispatched", False))

        patch_result = auto_patch_pipeline({"incident_id": unique_error_id, "strategy": "auto_hotfix"})
        self.assertIn("patch_id", patch_result)

        validation_result = patch_validator(patch_result)
        self.assertTrue(validation_result.get("is_valid", False))

        notification_status = incident_notification_bridge({
            "incident_id": unique_error_id,
            "status": "RECOVERED",
            "patch_id": patch_result.get("patch_id")
        })
        self.assertTrue(notification_status.get("sent", False))

        dashboard_output = recovery_dashboard_generator({
            "incident_id": unique_error_id,
            "resolution_status": "SUCCESS"
        })

        if isinstance(dashboard_output, dict) and "file_path" in dashboard_output:
            file_path = dashboard_output["file_path"]
            self.assertTrue(os.path.exists(file_path))
            os.remove(file_path)

if __name__ == "__main__":
    unittest.main()