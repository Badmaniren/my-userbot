import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io

from skills.preventive_recovery_gateway import PreventiveRecoveryGateway
from skills.preventive_patch_applier import PreventivePatchApplier
from skills.notification_channel_dispatcher import NotificationChannelDispatcher


class TestPreventiveRecoveryGateway(unittest.TestCase):

    def setUp(self):
        self.module_name = f"mod_{uuid.uuid4().hex[:8]}"
        self.channel_name = f"channel_{uuid.uuid4().hex[:8]}"
        self.incident_id = str(uuid.uuid4())
        self.error_message = f"err_{uuid.uuid4().hex}"
        self.log_level = random.choice(["CRITICAL", "EMERGENCY", "ALERT", "FATAL"])
        
        self.gateway = PreventiveRecoveryGateway()

    def test_gateway_initialization_and_composition(self):
        self.assertIsInstance(self.gateway.patch_applier, PreventivePatchApplier)
        self.assertIsInstance(self.gateway.dispatcher, NotificationChannelDispatcher)

    def test_run_preventive_recovery_cycle_success(self):
        expected_patch_result = {
            "status": "success",
            "module": self.module_name,
            "patches_applied": random.randint(1, 5),
            "token": uuid.uuid4().hex
        }
        expected_dispatch_result = True

        with patch.object(PreventivePatchApplier, 'run_preventive_cycle', return_value=expected_patch_result) as mock_patch, \
             patch.object(NotificationChannelDispatcher, 'dispatch', return_value=expected_dispatch_result) as mock_dispatch:
            
            result = self.gateway.execute_recovery_cycle(self.module_name, self.channel_name)

            mock_patch.assert_called_once_with(self.module_name)
            mock_dispatch.assert_called_once()
            
            self.assertIn("patch_result", result)
            self.assertIn("notification_dispatched", result)
            self.assertEqual(result["patch_result"], expected_patch_result)
            self.assertEqual(result["notification_dispatched"], expected_dispatch_result)

    def test_prevent_failures_and_broadcast(self):
        prevent_data = {
            "prevented": True,
            "incident_signature": uuid.uuid4().hex,
            "details": f"details_{uuid.uuid4().hex[:6]}"
        }
        broadcast_response = {
            self.channel_name: True,
            f"chan_{uuid.uuid4().hex[:4]}": True
        }

        with patch.object(PreventivePatchApplier, 'prevent_failures', return_value=prevent_data) as mock_prevent, \
             patch.object(NotificationChannelDispatcher, 'broadcast', return_value=broadcast_response) as mock_broadcast:

            result = self.gateway.secure_and_notify(self.module_name)

            mock_prevent.assert_called_once_with(self.module_name)
            mock_broadcast.assert_called_once()
            
            self.assertEqual(result["prevent_data"], prevent_data)
            self.assertEqual(result["broadcast_status"], broadcast_response)

    def test_stream_processing_with_gateway(self):
        random_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')
        stream_mock = io.BytesIO(random_bytes)
        
        parsed_stream_data = {
            "stream_id": uuid.uuid4().hex,
            "severity": self.log_level,
            "payload_data": random_bytes.decode('utf-8')
        }
        
        prevent_stream_result = {
            "status": "processed",
            "module_target": self.module_name
        }
        
        formatted_payload = {
            "level": self.log_level,
            "id": self.incident_id,
            "msg": self.error_message
        }

        with patch.object(NotificationChannelDispatcher, 'parse_stream_data', return_value=parsed_stream_data) as mock_parse, \
             patch.object(PreventivePatchApplier, 'prevent_failures_from_stream', return_value=prevent_stream_result) as mock_prevent_stream, \
             patch.object(NotificationChannelDispatcher, 'format_payload', return_value=formatted_payload) as mock_format, \
             patch.object(NotificationChannelDispatcher, 'dispatch', return_value=True) as mock_dispatch:

            res = self.gateway.handle_stream_incident(self.module_name, stream_mock, self.channel_name)

            mock_parse.assert_called_once_with(stream_mock)
            mock_prevent_stream.assert_called_once_with(self.module_name, stream_mock)
            mock_format.assert_called_once()
            mock_dispatch.assert_called_once_with(self.channel_name, formatted_payload)

            self.assertEqual(res["parsed_stream"], parsed_stream_data)
            self.assertEqual(res["prevent_result"], prevent_stream_result)
            self.assertTrue(res["dispatched"])

    def test_gateway_exception_handling_in_dispatch(self):
        expected_patch_result = {
            "status": "patched",
            "module": self.module_name
        }

        with patch.object(PreventivePatchApplier, 'apply_preventive_patches', return_value=expected_patch_result) as mock_patch, \
             patch.object(NotificationChannelDispatcher, 'dispatch', side_effect=Exception(self.error_message)) as mock_dispatch:

            result = self.gateway.apply_patches_with_safe_notification(self.module_name, self.channel_name)

            mock_patch.assert_called_once_with(self.module_name)
            mock_dispatch.assert_called_once()

            self.assertEqual(result["patch_result"], expected_patch_result)
            self.assertFalse(result["notification_dispatched"])
            self.assertIn("error", result)
            self.assertEqual(result["error"], self.error_message)


if __name__ == "__main__":
    unittest.main()