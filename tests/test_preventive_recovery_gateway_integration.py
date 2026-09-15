import unittest
import uuid
import random
from skills.preventive_recovery_gateway import PreventiveRecoveryGateway
from skills.preventive_patch_applier import PreventivePatchApplier
from skills.notification_channel_dispatcher import NotificationChannelDispatcher


class TestPreventiveRecoveryGatewayIntegration(unittest.TestCase):

    def setUp(self):
        self.patch_applier = PreventivePatchApplier()
        self.dispatcher = NotificationChannelDispatcher()
        self.gateway = PreventiveRecoveryGateway(
            patch_applier=self.patch_applier,
            dispatcher=self.dispatcher
        )
        self.module_name = f"test_module_{uuid.uuid4().hex[:8]}"
        self.channel_name = f"channel_{uuid.uuid4().hex[:8]}"

    def test_execute_recovery_cycle_integration(self):
        result = self.gateway.execute_recovery_cycle(self.module_name, self.channel_name)

        self.assertIn("patch_result", result)
        self.assertIn("notification_dispatched", result)
        self.assertIsInstance(result["patch_result"], dict)
        self.assertIsInstance(result["notification_dispatched"], bool)

    def test_secure_and_notify_integration(self):
        result = self.gateway.secure_and_notify(self.module_name)

        self.assertIn("prevent_data", result)
        self.assertIn("broadcast_status", result)
        self.assertIsInstance(result["prevent_data"], dict)
        self.assertIsInstance(result["broadcast_status"], dict)

    def test_handle_stream_incident_integration(self):
        stream_id = str(uuid.uuid4())
        severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        msg = f"Random error payload {uuid.uuid4().hex}"

        stream_mock = f'{{"stream_id": "{stream_id}", "severity": "{severity}", "payload_data": "{msg}"}}'

        result = self.gateway.handle_stream_incident(self.module_name, stream_mock, self.channel_name)

        self.assertIn("parsed_stream", result)
        self.assertIn("prevent_result", result)
        self.assertIn("dispatched", result)

        self.assertEqual(result["parsed_stream"].get("stream_id"), stream_id)
        self.assertEqual(result["parsed_stream"].get("severity"), severity)
        self.assertEqual(result["parsed_stream"].get("payload_data"), msg)
        self.assertIsInstance(result["dispatched"], bool)

    def test_apply_patches_with_safe_notification_integration(self):
        result = self.gateway.apply_patches_with_safe_notification(self.module_name, self.channel_name)

        self.assertIn("patch_result", result)
        self.assertIn("notification_dispatched", result)
        self.assertIsInstance(result["patch_result"], dict)
        self.assertIsInstance(result["notification_dispatched"], bool)

    def test_execute_preventive_cycle_integration(self):
        incident_id = uuid.uuid4().hex
        level = random.choice(["INFO", "WARNING", "CRITICAL"])
        message = f"Dynamic test message {uuid.uuid4().hex}"

        result = self.gateway.execute_preventive_cycle(
            module_name=self.module_name,
            channel_name=self.channel_name,
            level=level,
            incident_id=incident_id,
            message=message
        )

        self.assertIn("patch_execution", result)
        self.assertIn("notification_dispatch", result)
        self.assertIsInstance(result["patch_execution"], dict)
        self.assertIsInstance(result["notification_dispatch"], bool)
        self.assertTrue(result["notification_dispatch"])

        self.assertIn(self.channel_name, self.dispatcher.channels)


if __name__ == "__main__":
    unittest.main()