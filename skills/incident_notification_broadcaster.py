from datetime import datetime
from skills.incident_notification_bridge import IncidentNotificationBridge
from skills.notification_channel_dispatcher import NotificationChannelDispatcher


class IncidentNotificationBroadcaster:
    def __init__(self, bridge: IncidentNotificationBridge, dispatcher: NotificationChannelDispatcher):
        self.bridge = bridge
        self.dispatcher = dispatcher

    def broadcast(self, incident_id=None, threshold=None, recipient=None, channel=None, **kwargs):
        payload = {
            "incident_id": incident_id,
            "threshold": threshold,
            "recipient": recipient,
            "channel": channel,
        }
        if channel and self.dispatcher and channel in getattr(self.dispatcher, "channels", {}):
            res = self.dispatcher.dispatch(channel, payload)
            return {"status": "dispatched" if res else "failed", "result": res}
        if self.bridge:
            self.bridge.process_incident(payload, channel=channel)
        return {"status": "dispatched"}

    def broadcast_incident(self, incident_id: str, level: str, message: str, channel: str):
        payload = self.dispatcher.format_payload(level, incident_id, message)
        broadcast_result = self.dispatcher.broadcast(payload)
        self.bridge.process_incident(payload, channel, None)
        return broadcast_result

    def ingest_and_broadcast_stream(self, stream_mock, channel: str):
        self.dispatcher.parse_stream_data(stream_mock)
        return self.bridge.ingest_stream(stream_mock, channel)

    def dispatch_critical(self, aggregated_incident: dict):
        _ = datetime.now().isoformat()
        return self.bridge.dispatch_critical_incident(aggregated_incident)

    def register_channel(self, channel_name: str, config: dict):
        self.dispatcher.register_channel(channel_name, config)

    def broadcast_to_webhooks(self, url: str, payload: dict):
        return self.bridge.broadcast_to_webhooks(url, payload)

    def broadcast_critical_incident(self, aggregated_incident: dict):
        # Метод для интеграционного теста, использующий реальные возможности моста и диспетчера
        # Например, определяем канал из диспетчера или отправляем через bridge
        channels = getattr(self.dispatcher, 'channels', {})
        results = {}
        for channel_name in channels:
            payload = aggregated_incident.get("payload") or self.dispatcher.format_payload(
                aggregated_incident.get("level", "INFO"),
                aggregated_incident.get("incident_id", "UNKNOWN"),
                aggregated_incident.get("message", "")
            )
            res = self.bridge.process_incident(payload, channel_name, None)
            results[channel_name] = res
        return results