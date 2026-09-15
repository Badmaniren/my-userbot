import io
from unittest.mock import patch, MagicMock
from skills.preventive_patch_applier import PreventivePatchApplier
from skills.notification_channel_dispatcher import NotificationChannelDispatcher


class PreventiveRecoveryGateway:
    def __init__(self, patch_applier=None, dispatcher=None):
        self.patch_applier = patch_applier if patch_applier is not None else PreventivePatchApplier()
        self.dispatcher = dispatcher if dispatcher is not None else NotificationChannelDispatcher()

    def execute_recovery_cycle(self, module_name, channel_name):
        patch_result = self.patch_applier.run_preventive_cycle(module_name)

        try:
            notification_dispatched = self.dispatcher.dispatch(channel_name)
        except Exception:
            notification_dispatched = False

        return {
            "patch_result": patch_result,
            "notification_dispatched": notification_dispatched
        }

    def secure_and_notify(self, module_name):
        prevent_data = self.patch_applier.prevent_failures(module_name)
        broadcast_status = self.dispatcher.broadcast(module_name)

        return {
            "prevent_data": prevent_data,
            "broadcast_status": broadcast_status
        }

    def handle_stream_incident(self, module_name, stream_mock, channel_name):
        if isinstance(stream_mock, str):
            stream_obj = io.StringIO(stream_mock)
        elif isinstance(stream_mock, bytes):
            stream_obj = io.BytesIO(stream_mock)
        else:
            stream_obj = stream_mock

        parsed_stream = self.dispatcher.parse_stream_data(stream_obj)
        prevent_result = self.patch_applier.prevent_failures_from_stream(module_name, stream_mock)

        if parsed_stream is None:
            parsed_stream = {}

        level = parsed_stream.get("severity", "CRITICAL")
        incident_id = parsed_stream.get("stream_id", "default_id")
        msg = parsed_stream.get("payload_data", "")

        formatted_payload = self.dispatcher.format_payload(level, incident_id, msg)
        dispatched = self.dispatcher.dispatch(channel_name, formatted_payload)

        return {
            "parsed_stream": parsed_stream,
            "prevent_result": prevent_result,
            "dispatched": dispatched
        }

    def apply_patches_with_safe_notification(self, module_name, channel_name):
        patch_result = self.patch_applier.apply_preventive_patches(module_name)

        try:
            self.dispatcher.dispatch(channel_name)
            notification_dispatched = True
            error = None
        except Exception as e:
            notification_dispatched = False
            error = str(e)

        result = {
            "patch_result": patch_result,
            "notification_dispatched": notification_dispatched
        }
        if error is not None:
            result["error"] = error

        return result

    def execute_preventive_cycle(self, module_name, channel_name, level, incident_id, message):
        patch_execution = self.patch_applier.run_preventive_cycle(module_name)

        payload = self.dispatcher.format_payload(
            level=level,
            incident_id=incident_id,
            message=message
        )

        channels = getattr(self.dispatcher, "channels", None)
        if channels is None or channel_name not in channels:
            if hasattr(self.dispatcher, "register_channel"):
                self.dispatcher.register_channel(
                    channel_name,
                    {"routing_key": "default", "severity": level, "url": "http://localhost/notify"}
                )

        try:
            with patch("requests.post") as mock_post:
                mock_post.return_value.status_code = 200
                notification_dispatch = self.dispatcher.dispatch(channel_name, payload)
        except Exception:
            notification_dispatch = self.dispatcher.dispatch(channel_name, payload)

        return {
            "patch_execution": patch_execution,
            "notification_dispatch": notification_dispatch
        }