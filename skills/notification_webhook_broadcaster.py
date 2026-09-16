from skills.notification_channel_dispatcher import NotificationChannelDispatcher
from skills.notification_template_engine import NotificationTemplateEngine

class NotificationWebhookBroadcaster:
    def __init__(self):
        self.dispatcher = NotificationChannelDispatcher()
        self.template_engine = NotificationTemplateEngine()

    def post(self, payload_data, channel_name="webhook"):
        payload = payload_data if isinstance(payload_data, dict) else {"payload": payload_data}
        return self.dispatch_to_webhook(channel_name, payload)

    def broadcast_incident(self, severity, incident_id, raw_data, template_name):
        payload = self.template_engine.generate_notification_payload(severity, incident_id, raw_data)
        rendered_text = self.template_engine.render_text(payload, template_name)
        payload["rendered_text"] = rendered_text
        return self.dispatcher.broadcast(payload)

    def register_webhook_channel(self, channel_name, config):
        return self.dispatcher.register_channel(channel_name, config)

    def dispatch_to_webhook(self, channel_name, payload):
        return self.dispatcher.dispatch(channel_name, payload)

    def process_stream_and_broadcast(self, stream, severity):
        parsed_data = self.template_engine.parse_stream_data(stream)
        return self.dispatcher.broadcast(parsed_data)

    def export_notification_report(self, context, file_path):
        return self.template_engine.export_notification_file(context, file_path)