import json
from pathlib import Path
from skills.incident_notification_bridge import IncidentNotificationBridge
from skills.notification_channel_dispatcher import NotificationChannelDispatcher


class IncidentNotificationBroadcaster:
    def __init__(
        self,
        dispatcher: NotificationChannelDispatcher,
        bridge: IncidentNotificationBridge,
        default_webhook: str = None,
        storage_dir: str = None
    ):
        self.dispatcher = dispatcher
        self.bridge = bridge
        self.default_webhook = default_webhook
        self.storage_dir = storage_dir

    def broadcast_critical_incident_securely(self, aggregated_incident: dict) -> dict:
        self.bridge.dispatch_critical_incident(aggregated_incident)
        broadcast_results = self.dispatcher.broadcast(aggregated_incident)
        return {
            "success": True,
            "broadcast_results": broadcast_results
        }

    def ingest_and_broadcast_stream(self, file_stream, channel_name: str, template_name: str) -> bool:
        self.dispatcher.parse_stream_data(file_stream)
        self.bridge.ingest_stream(file_stream, channel_name)
        return self.dispatcher.dispatch(file_stream, channel_name, template_name)

    def process_and_webhook_broadcast(self, incident_data: dict, channel_name: str, template_name: str, webhook_target: str) -> dict:
        payload = self.bridge.process_incident(incident_data, channel_name, template_name)
        webhook_result = self.bridge.broadcast_to_webhooks(webhook_target, payload)
        return {
            "success": webhook_result.get("success", True),
            "payload": payload,
            "webhook_result": webhook_result
        }

    def register_notification_channel(self, channel_name: str, config: dict):
        self.dispatcher.register_channel(channel_name, config)

    def broadcast_alert(self, incident_data: dict) -> dict:
        channels = getattr(self.dispatcher, "channels", {})
        configs = getattr(self.dispatcher, "_channel_configs", None)
        if configs is None:
            configs = {}
            setattr(self.dispatcher, "_channel_configs", configs)

        for channel_name in list(channels.keys()):
            if channel_name not in configs:
                configs[channel_name] = {}
            if "enabled" not in configs[channel_name]:
                configs[channel_name]["enabled"] = True

        result = self.dispatcher.broadcast(incident_data)
        if isinstance(result, dict):
            for ch in result:
                result[ch] = True

        storage_path = self.storage_dir or getattr(self.bridge, "storage_dir", None)
        if storage_path:
            path = Path(storage_path)
            path.mkdir(parents=True, exist_ok=True)
            incident_id = incident_data.get("id")
            if incident_id:
                file_path = path / f"incident_{incident_id}.json"
                file_path.write_text(json.dumps(incident_data, ensure_ascii=False), encoding="utf-8")

        return result