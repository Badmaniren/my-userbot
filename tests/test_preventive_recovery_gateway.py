import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import string

from skills.preventive_recovery_gateway import PreventiveRecoveryGateway
from skills.preventive_patch_applier import PreventivePatchApplier
from skills.notification_channel_dispatcher import NotificationChannelDispatcher


class TestPreventiveRecoveryGateway(unittest.TestCase):

    def setUp(self):
        self.mock_patch_applier = MagicMock(spec=PreventivePatchApplier)
        self.mock_dispatcher = MagicMock(spec=NotificationChannelDispatcher)
        self.gateway = PreventiveRecoveryGateway(
            patch_applier=self.mock_patch_applier,
            dispatcher=self.mock_dispatcher
        )
        self.module_name = f"mod_{uuid.uuid4().hex[:8]}"
        self.channel_name = f"chan_{uuid.uuid4().hex[:8]}"
        self.incident_id = str(uuid.uuid4())
        self.message = ''.join(random.choices(string.ascii_letters + " ", k=15))
        self.level = random.choice(["CRITICAL", "HIGH", "WARNING", "INFO"])

    def test_init_default_dependencies(self):
        gateway = PreventiveRecoveryGateway()
        self.assertIsInstance(gateway.patch_applier, PreventivePatchApplier)
        self.assertIsInstance(gateway.dispatcher, NotificationChannelDispatcher)

    def test_execute_recovery_cycle_success(self):
        expected_patch_result = {"status": uuid.uuid4().hex, "patched": True}
        self.mock_patch_applier.run_preventive_cycle.return_value = expected_patch_result
        self.mock_dispatcher.dispatch.return_value = True

        result = self.gateway.execute_recovery_cycle(self.module_name, self.channel_name)

        self.mock_patch_applier.run_preventive_cycle.assert_called_once_with(self.module_name)
        self.mock_dispatcher.dispatch.assert_called_once_with(self.channel_name)
        self.assertEqual(result["patch_result"], expected_patch_result)
        self.assertTrue(result["notification_dispatched"])

    def test_execute_recovery_cycle_dispatch_exception(self):
        expected_patch_result = {"status": uuid.uuid4().hex, "patched": False}
        self.mock_patch_applier.run_preventive_cycle.return_value = expected_patch_result

        err_msg = f"err_{uuid.uuid4().hex}"
        self.mock_dispatcher.dispatch.side_effect = Exception(err_msg)

        result = self.gateway.execute_recovery_cycle(self.module_name, self.channel_name)

        self.mock_patch_applier.run_preventive_cycle.assert_called_once_with(self.module_name)
        self.mock_dispatcher.dispatch.assert_called_once_with(self.channel_name)
        self.assertEqual(result["patch_result"], expected_patch_result)
        self.assertFalse(result["notification_dispatched"])

    def test_secure_and_notify(self):
        prevent_data_mock = {"prevent_key": uuid.uuid4().hex}
        broadcast_status_mock = {"channel_1": random.choice([True, False])}

        self.mock_patch_applier.prevent_failures.return_value = prevent_data_mock
        self.mock_dispatcher.broadcast.return_value = broadcast_status_mock

        result = self.gateway.secure_and_notify(self.module_name)

        self.mock_patch_applier.prevent_failures.assert_called_once_with(self.module_name)
        self.mock_dispatcher.broadcast.assert_called_once_with(self.module_name)
        self.assertEqual(result["prevent_data"], prevent_data_mock)
        self.assertEqual(result["broadcast_status"], broadcast_status_mock)

    def test_handle_stream_incident(self):
        stream_mock = {"raw_stream": uuid.uuid4().hex}
        parsed_stream_mock = {
            "severity": self.level,
            "stream_id": self.incident_id,
            "payload_data": self.message
        }
        prevent_result_mock = {"prevented": True, "id": uuid.uuid4().hex}
        formatted_payload_mock = {"formatted": uuid.uuid4().hex}

        self.mock_dispatcher.parse_stream_data.return_value = parsed_stream_mock
        self.mock_patch_applier.prevent_failures_from_stream.return_value = prevent_result_mock
        self.mock_dispatcher.format_payload.return_value = formatted_payload_mock
        self.mock_dispatcher.dispatch.return_value = True

        result = self.gateway.handle_stream_incident(self.module_name, stream_mock, self.channel_name)

        self.mock_dispatcher.parse_stream_data.assert_called_once_with(stream_mock)
        self.mock_patch_applier.prevent_failures_from_stream.assert_called_once_with(self.module_name, stream_mock)
        self.mock_dispatcher.format_payload.assert_called_once_with(self.level, self.incident_id, self.message)
        self.mock_dispatcher.dispatch.assert_called_once_with(self.channel_name, formatted_payload_mock)

        self.assertEqual(result["parsed_stream"], parsed_stream_mock)
        self.assertEqual(result["prevent_result"], prevent_result_mock)
        self.assertTrue(result["dispatched"])

    def test_apply_patches_with_safe_notification_success(self):
        patch_result_mock = {"applied": True, "details": uuid.uuid4().hex}
        self.mock_patch_applier.apply_preventive_patches.return_value = patch_result_mock
        self.mock_dispatcher.dispatch.return_value = True

        result = self.gateway.apply_patches_with_safe_notification(self.module_name, self.channel_name)

        self.mock_patch_applier.apply_preventive_patches.assert_called_once_with(self.module_name)
        self.mock_dispatcher.dispatch.assert_called_once_with(self.channel_name)
        self.assertEqual(result["patch_result"], patch_result_mock)
        self.assertTrue(result["notification_dispatched"])
        self.assertNotIn("error", result)

    def test_apply_patches_with_safe_notification_failure(self):
        patch_result_mock = {"applied": False}
        self.mock_patch_applier.apply_preventive_patches.return_value = patch_result_mock
        error_message = f"fail_{uuid.uuid4().hex}"
        self.mock_dispatcher.dispatch.side_effect = RuntimeError(error_message)

        result = self.gateway.apply_patches_with_safe_notification(self.module_name, self.channel_name)

        self.mock_patch_applier.apply_preventive_patches.assert_called_once_with(self.module_name)
        self.mock_dispatcher.dispatch.assert_called_once_with(self.channel_name)
        self.assertEqual(result["patch_result"], patch_result_mock)
        self.assertFalse(result["notification_dispatched"])
        self.assertEqual(result["error"], error_message)

    def test_execute_preventive_cycle_channel_unregistered(self):
        patch_execution_mock = {"executed": True, "token": uuid.uuid4().hex}
        payload_mock = {"msg": uuid.uuid4().hex}
        dispatch_status = random.choice([True, False])

        self.mock_patch_applier.run_preventive_cycle.return_value = patch_execution_mock
        self.mock_dispatcher.format_payload.return_value = payload_mock
        self.mock_dispatcher.channels = {}
        self.mock_dispatcher.dispatch.return_value = dispatch_status

        result = self.gateway.execute_preventive_cycle(
            self.module_name, self.channel_name, self.level, self.incident_id, self.message
        )

        self.mock_patch_applier.run_preventive_cycle.assert_called_once_with(self.module_name)
        self.mock_dispatcher.format_payload.assert_called_once_with(
            level=self.level,
            incident_id=self.incident_id,
            message=self.message
        )
        self.mock_dispatcher.register_channel.assert_called_once_with(
            self.channel_name, {"routing_key": "default", "severity": self.level, "url": "http://localhost/notify"}
        )
        self.mock_dispatcher.dispatch.assert_called_once_with(self.channel_name, payload_mock)
        self.assertEqual(result["patch_execution"], patch_execution_mock)
        self.assertEqual(result["notification_dispatch"], dispatch_status)

    def test_execute_preventive_cycle_channel_registered(self):
        patch_execution_mock = {"executed": False}
        payload_mock = {"payload_id": uuid.uuid4().hex}
        dispatch_status = True

        self.mock_patch_applier.run_preventive_cycle.return_value = patch_execution_mock
        self.mock_dispatcher.format_payload.return_value = payload_mock
        self.mock_dispatcher.channels = {self.channel_name: {"routing_key": "custom"}}
        self.mock_dispatcher.dispatch.return_value = dispatch_status

        result = self.gateway.execute_preventive_cycle(
            self.module_name, self.channel_name, self.level, self.incident_id, self.message
        )

        self.mock_patch_applier.run_preventive_cycle.assert_called_once_with(self.module_name)
        self.mock_dispatcher.format_payload.assert_called_once_with(
            level=self.level,
            incident_id=self.incident_id,
            message=self.message
        )
        self.mock_dispatcher.register_channel.assert_not_called()
        self.mock_dispatcher.dispatch.assert_called_once_with(self.channel_name, payload_mock)
        self.assertEqual(result["patch_execution"], patch_execution_mock)
        self.assertEqual(result["notification_dispatch"], dispatch_status)


if __name__ == "__main__":
    unittest.main()