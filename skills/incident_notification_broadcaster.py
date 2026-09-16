from skills.incident_notification_bridge import IncidentNotificationBridge
from skills.notification_channel_dispatcher import NotificationChannelDispatcher

class IncidentNotificationBroadcaster:
    def __init__(self, bridge: IncidentNotificationBridge, dispatcher: NotificationChannelDispatcher = None):
        self.bridge = bridge
        if dispatcher is not None:
            self.dispatcher = dispatcher
        else:
            self.dispatcher = bridge.dispatcher

    def broadcast_incident(self, payload_data: dict, channel: str, template_engine=None):
        if template_engine is not None and hasattr(template_engine, 'render'):
            template_engine.render(payload_data)
        return self.dispatcher.broadcast(payload_data)

    def process_stream_broadcast(self, stream, channel: str):
        return self.bridge.ingest_stream(stream, channel)

    def handle_critical_broadcast(self, aggregated_payload: dict):
        return self.bridge.dispatch_critical_incident(aggregated_payload)

    def forward_to_webhook(self, webhook_url: str, payload_dict: dict):
        return self.bridge.broadcast_to_webhooks(webhook_url, payload_dict)

    def execute_broadcast(self, incident_data: dict, channel: str, template: str = "standard_alert"):
        if self.bridge.template_engine is not None and hasattr(self.bridge.template_engine, 'render'):
            self.bridge.template_engine.render(incident_data)

        broadcast_result = self.dispatcher.broadcast(incident_data)

        if hasattr(self.bridge, 'persist_incident'):
            self.bridge.persist_incident(incident_data)
        elif hasattr(self.bridge, 'store_incident'):
            self.bridge.store_incident(incident_data)

        return broadcast_result