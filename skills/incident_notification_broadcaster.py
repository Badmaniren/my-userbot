from skills.incident_severity_evaluator import IncidentSeverityEvaluator
from skills.incident_notification_bridge import IncidentNotificationBridge


class IncidentNotificationBroadcaster:
    def __init__(self, severity_evaluator=None, notification_bridge=None, evaluator=None, bridge=None):
        self.evaluator = severity_evaluator if severity_evaluator is not None else evaluator
        if self.evaluator is None:
            self.evaluator = IncidentSeverityEvaluator()

        self.bridge = notification_bridge if notification_bridge is not None else bridge
        if self.bridge is None:
            self.bridge = IncidentNotificationBridge()

    def process_and_broadcast(self, module_name, exception, traceback_str, incident_id=None, webhook_url=None, channel=None, template=None):
        try:
            evaluated = self.evaluator.evaluate(module_name, exception, traceback_str, incident_id)

            inc_id = incident_id if incident_id is not None else evaluated.get('incident_id')
            if inc_id and 'incident_id' not in evaluated:
                evaluated['incident_id'] = inc_id

            if 'severity_score' not in evaluated and 'severity' in evaluated:
                evaluated['severity_score'] = evaluated['severity']

            severity = evaluated.get('severity_score') or evaluated.get('severity')

            kwargs = {}
            if webhook_url is not None:
                kwargs['webhook_url'] = webhook_url

            self.bridge.process_incident(evaluated, channel, template, **kwargs)

            return {
                'status': 'success',
                'incident_id': inc_id,
                'severity': severity
            }
        except Exception as e:
            return {
                'status': 'error',
                'error_message': str(e)
            }

    def ingest_and_broadcast_stream(self, module_name, file_stream, channel=None, webhook_url=None):
        aggregated = self.evaluator.evaluate_stream(module_name, file_stream)
        self.bridge.ingest_stream(module_name, file_stream)
        self.bridge.dispatch_critical_incident(aggregated)

        return {
            'module': module_name,
            'broadcast_target': webhook_url
        }


def broadcast_incident_pipeline(module_name, exception, traceback_str, incident_id=None, channel=None, template=None):
    broadcaster = IncidentNotificationBroadcaster()
    evaluated = broadcaster.evaluator.evaluate(module_name, exception, traceback_str, incident_id)

    inc_id = incident_id if incident_id is not None else evaluated.get('incident_id')
    if inc_id and 'incident_id' not in evaluated:
        evaluated['incident_id'] = inc_id

    if 'severity_score' not in evaluated and 'severity' in evaluated:
        evaluated['severity_score'] = evaluated['severity']

    broadcaster.bridge.process_incident(evaluated, channel, template)
    return evaluated