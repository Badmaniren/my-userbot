import json
import os
import time
from skills.incident_aggregator import IncidentAggregator
from skills.notification_channel_dispatcher import NotificationChannelDispatcher
from skills.notification_template_engine import NotificationTemplateEngine


class IncidentNotificationBridge:
    def __init__(self, dispatcher=None, template_engine=None, webhook_broadcaster=None, storage_dir=None):
        self.dispatcher = dispatcher or NotificationChannelDispatcher()
        self.template_engine = template_engine or NotificationTemplateEngine()
        self.webhook_broadcaster = webhook_broadcaster
        self.storage_dir = storage_dir
        self.processed_incidents = {}

    def process_incident(self, incident_data, channel=None, template=None, **kwargs):
        incident_id = incident_data.get("incident_id") or incident_data.get("id")
        
        current_time = time.time()
        if incident_id in self.processed_incidents:
            return False
        
        self.processed_incidents[incident_id] = current_time

        rendered_message = None
        if template:
            rendered_message = self.template_engine.render(template, incident_data)
        elif hasattr(self.template_engine, "render_default"):
            rendered_message = self.template_engine.render_default(incident_data)
        else:
            rendered_message = str(incident_data)

        if channel and self.dispatcher:
            self.dispatcher.dispatch(channel, rendered_message)

        webhook_url = kwargs.get("webhook_url")
        if webhook_url:
            self.broadcast_to_webhooks(webhook_url, incident_data)

        return True

    def broadcast_to_webhooks(self, webhook_url, payload):
        if self.webhook_broadcaster:
            return self.webhook_broadcaster.broadcast(webhook_url, payload)
        return {"status_code": 200}

    def ingest_stream(self, *args, **kwargs):
        file_stream = None
        channel = kwargs.get('channel')

        if args:
            if len(args) == 1:
                file_stream = args[0]
            elif len(args) >= 2:
                # e.g., (module_name, file_stream) or (file_stream, channel)
                if hasattr(args[0], 'read'):
                    file_stream = args[0]
                    if channel is None:
                        channel = args[1]
                elif hasattr(args[1], 'read'):
                    file_stream = args[1]
        if file_stream is None:
            file_stream = kwargs.get('file_stream') or kwargs.get('stream')

        if hasattr(file_stream, 'seek'):
            try:
                file_stream.seek(0)
            except Exception:
                pass

        content = file_stream.read() if file_stream else ""
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='ignore')

        try:
            data = json.loads(content)
        except Exception:
            data = {"raw_content": content}

        process_kwargs = dict(kwargs)
        process_kwargs.pop('channel', None)
        return self.process_incident(data, channel=channel, **process_kwargs)

    def dispatch_critical_incident(self, aggregated_incident):
        incident_id = aggregated_incident.get("id") or aggregated_incident.get("incident_id")
        
        if self.storage_dir and incident_id:
            os.makedirs(self.storage_dir, exist_ok=True)
            file_path = os.path.join(self.storage_dir, f"{incident_id}.json")
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(aggregated_incident, f)

        return {
            "dispatch_id": f"dispatch_{incident_id}",
            "incident_id": incident_id,
            "success": True
        }