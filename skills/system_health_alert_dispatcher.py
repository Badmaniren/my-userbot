import uuid
import datetime
import io
import os

from skills.system_health_aggregator import system_health_aggregator
from skills.system_health_telemetry_collector import system_health_telemetry_collector
from skills.incident_aggregator import incident_aggregator
from skills.notification_channel_dispatcher import notification_channel_dispatcher

class SystemHealthAlertDispatcher:
    def __init__(self, channel_dispatcher=None, template_engine=None, webhook_broadcaster=None):
        self.channel_dispatcher = channel_dispatcher
        self.template_engine = template_engine
        self.webhook_broadcaster = webhook_broadcaster

    def dispatch_alert(self, alert_id, severity, payload, recipient):
        rendered_content = self.template_engine.render(
            template_name="critical_alert",
            context={"alert_id": alert_id, "severity": severity, "payload": payload}
        )
        success = self.channel_dispatcher.send(
            recipient=recipient,
            content=rendered_content
        )
        return success

    def dispatch_with_webhook(self, alert_id, severity, payload, webhook_url):
        rendered_content = self.template_engine.render(
            template_name="critical_alert",
            context={"alert_id": alert_id, "severity": severity, "payload": payload}
        )
        response = self.webhook_broadcaster.broadcast(webhook_url, alert_id=alert_id, payload=rendered_content)
        return {"success": True, "response": response}

    def _sort_alerts_by_severity(self, alerts):
        severity_weights = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1}
        return sorted(alerts, key=lambda x: severity_weights.get(x.get("severity", "LOW"), 0), reverse=True)

    def dispatch_batch(self, alerts):
        sorted_alerts = self._sort_alerts_by_severity(alerts)
        return self.channel_dispatcher.batch_send(sorted_alerts)

    def process_stream(self, stream: io.BytesIO):
        content = stream.read().decode('utf-8')
        lines = content.strip().split('\n')
        count = 0
        for line in lines:
            if not line:
                continue
            parts = line.split('|')
            alert_data = {}
            for part in parts:
                if ':' in part:
                    k, v = part.split(':', 1)
                    alert_data[k.strip()] = v.strip()
            
            alert_id = alert_data.get('ALERT_ID', uuid.uuid4().hex)
            severity = alert_data.get('SEV', 'CRITICAL')
            msg = alert_data.get('MSG', '')
            
            rendered = self.template_engine.render(
                template_name="stream_alert",
                context={"alert_id": alert_id, "severity": severity, "payload": msg}
            )
            self.channel_dispatcher.send(recipient="stream_recipient", content=rendered)
            count += 1
        return count


def system_health_alert_dispatcher(incident, channels, verify_delivery=True):
    node_id = incident.get("node_id", str(uuid.uuid4()))
    error_code = incident.get("error_code", "ERR-0000")
    
    dispatch_id = uuid.uuid4().hex
    log_file_path = None
    
    if verify_delivery:
        log_file_path = f"dispatch_{dispatch_id}.log"
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(f"Node ID: {node_id}\nError Code: {error_code}\n")
            
    result = {
        "dispatch_id": dispatch_id,
        "status": "dispatched",
        "node_id": node_id
    }
    if log_file_path:
        result["log_file_path"] = log_file_path
        
    return result