import unittest
import uuid
import random
from skills.preventive_patch_applier import PreventivePatchApplier
from skills.notification_channel_dispatcher import NotificationChannelDispatcher
from skills.preventive_recovery_gateway import PreventiveRecoveryGateway

class DummyForecaster:
    def forecast_trends(self, module_name):
        return {"status": "analyzed", "risk_level": "high"}

class DummyRecoveryHub:
    def register_incident(self, incident_data):
        return {"registered": True, "id": incident_data.get("id")}

class TestPreventiveRecoveryGatewayIntegration(unittest.TestCase):
    def setUp(self):
        self.forecaster = DummyForecaster()
        self.recovery_hub = DummyRecoveryHub()
        
        # Real instances of the required skills (No mocks between them)
        self.patch_applier = PreventivePatchApplier(self.forecaster, self.recovery_hub)
        self.dispatcher = NotificationChannelDispatcher()
        
        # Target gateway composition
        self.gateway = PreventiveRecoveryGateway(
            patch_applier=self.patch_applier,
            dispatcher=self.dispatcher
        )

    def test_integration_preventive_flow_success(self):
        # Generate completely random inputs to prevent hardcoded bypasses
        random_id = str(uuid.uuid4())
        module_name = f"auth_service_{uuid.uuid4().hex[:8]}"
        channel_name = f"pagerduty_{uuid.uuid4().hex[:8]}"
        incident_id = f"INC-{random.randint(10000, 99999)}-{uuid.uuid4().hex[:4]}"
        alert_message = f"Potential memory leak detected in {module_name} with signature {random_id}"
        channel_config = {
            "routing_key": f"key_{uuid.uuid4().hex}",
            "severity": "critical"
        }

        # Step 1: Register notification channel via dispatcher inside the gateway
        registration_result = self.gateway.dispatcher.register_channel(channel_name, channel_config)
        
        # Step 2: Run the integrated gateway cycle
        # This must trigger patch application and dispatch notifications
        flow_result = self.gateway.execute_preventive_cycle(
            module_name=module_name,
            channel_name=channel_name,
            level="CRITICAL",
            incident_id=incident_id,
            message=alert_message
        )

        # Step 3: Assertions verifying real data propagation and integration
        self.assertIsInstance(flow_result, dict)
        self.assertIn("patch_execution", flow_result)
        self.assertIn("notification_dispatch", flow_result)
        
        # Verify patch applier output structure
        patch_data = flow_result["patch_execution"]
        self.assertIsInstance(patch_data, dict)
        
        # Verify notification dispatch output
        dispatch_status = flow_result["notification_dispatch"]
        self.assertTrue(dispatch_status)

        # Verify payload formatting integrity (ensuring random values are preserved)
        formatted_payload = self.gateway.dispatcher.format_payload(
            level="CRITICAL",
            incident_id=incident_id,
            message=alert_message
        )
        self.assertEqual(formatted_payload["incident_id"], incident_id)
        self.assertIn(random_id, formatted_payload["message"])
        self.assertEqual(formatted_payload["level"], "CRITICAL")

if __name__ == "__main__":
    unittest.main()